import datetime
import os

import jwt
from flask import request, jsonify
from flask_marshmallow import Marshmallow
from marshmallow import post_load, ValidationError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from app import app
from models.models import User, db, Post

ma = Marshmallow(app)


class UserSchema(ma.Schema):
    class Meta:
        model = User
        fields = ("id", "username", "email", "imageUrl", "password")


class UserDisplaySchema(ma.Schema):
    class Meta:
        model = User
        fields = ("id", "username", "email", "imageUrl")


class UserSignupSchema(ma.Schema):
    class Meta:
        model = User
        fields = ("username", "email", "password")

    @post_load
    def make_user(self, data, **kwargs):
        return User(**data)


class PostSchema(ma.Schema):
    class Meta:
        model = Post
        fields = ("id", "title", "description", "imageUrl", "timeCreated", "author", "archived")

    author = ma.Nested(UserDisplaySchema)


class PostCreateSchema(ma.Schema):
    class Meta:
        model = Post
        fields = ("title", "description", "author_id")

    @post_load
    def make_post(self, data, **kwargs):
        return Post(**data)


user_schema = UserSchema()
user_signup_schema = UserSignupSchema()
user_display_schema = UserDisplaySchema()
post_schema = PostSchema()
posts_schema = PostSchema(many=True)
post_create_schema = PostCreateSchema()


def validate_token(func):
    def w_func(*args, **kwargs):
        token = None
        if "x-token" in request.headers:
            token = request.headers["x-token"]
        if not token:
            return jsonify({"message": "token_absent"}), 401
        try:
            decoded_data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=['HS256'])
            user_id_from_token = decoded_data["user_id"]
            user = User.query.filter(User.id == user_id_from_token).first()
            kwargs["user_from_token"] = user
            val = func(*args, **kwargs)
        except Exception as e:
            print(e)
            return jsonify({"message": "invalid_token"}), 401
        return val

    w_func.__name__ = func.__name__

    return w_func


# -------------------------------User Routes--------------------------------

@app.route("/api/user/signup", methods=["POST"])
def api_user_signup():
    try:
        user_from_request = request.json
        user = user_signup_schema.load(user_from_request)
        if user:
            hashed_password = generate_password_hash(user.password, method="sha256")
            user.password = hashed_password
            db.session.add(user)
            db.session.commit()
            token = jwt.encode(
                {"user_id": user.id,
                 "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30)},
                app.config["SECRET_KEY"]
            )
            return {"user": user_display_schema.dump(user), "token": token}
    except ValidationError:
        return jsonify({"message": "bad_request"}), 400
    except Exception as e:
        print("Exception", e)
        return jsonify({"message": "internal_server_error"}), 500


@app.route("/api/user/update", methods=["PUT"])
@validate_token
def api_user_update(user_from_token):
    try:
        data_from_request = request.json
        if check_password_hash(user_from_token.password, data_from_request["password"]):
            user_from_token.username = data_from_request["username"]
            user_from_token.password = generate_password_hash(data_from_request["password"], method="sha256")
            db.session.add(user_from_token)
            db.session.commit()
            return {"message": "user_updated"}, 201
    except Exception as e:
        print(e)
        return {"message": "error"}, 500


@app.route("/api/user/delete", methods=["DELETE"])
@validate_token
def api_user_delete(user_from_token):
    try:
        data_from_request = request.json
        if check_password_hash(user_from_token.password, data_from_request["password"]):
            db.session.delete(user_from_token)
            db.session.commit()
            return {"message": "user_deleted"}, 200
    except Exception as e:
        print(e)
        return {"message": "error"}, 500


@app.route("/api/user/update-profile-pic", methods=["POST"])
@validate_token
def api_user_prof_pic(user_from_token):
    try:
        file = request.files["file"]
        file_ext = file.filename[file.filename.rfind('.'):]
        s_fname = secure_filename(str(user_from_token.id) + file_ext)
        file.save(os.path.join(app.config['UPLOADS_DIR'] + "user_thumbs", s_fname))
        user_from_token.imageUrl = os.path.join(app.config['UPLOADS_DIR'] + "user_thumbs", s_fname)
        db.session.add(user_from_token)
        db.session.commit()
        return jsonify({"message": "file_saved"})
    except Exception as e:
        print(e)
        return jsonify({"message": "bad_request"}), 400


@app.route('/api/user/login', methods=["POST"])
def api_user_login():
    body_data = request.get_json()
    if body_data["email"] and body_data["password"]:
        email_from_request = body_data["email"]
        password_from_request = body_data["password"]
        user = User.query.filter(User.email == email_from_request).first()
        if user and check_password_hash(user.password, password_from_request):
            token = jwt.encode(
                {"user_id": user.id,
                 "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30)},
                app.config["SECRET_KEY"]
            )
            return jsonify({"status": "login_success", "token": token}), 200
        return {"status": "invalid_credentials"}, 400
    return {"status": "invalid_data"}, 400


@app.route('/api/user/<uid>', methods=["GET"])
@validate_token
def api_user_get(uid, user_from_token):
    requested_user = User.query.filter(User.id == int(uid)).first()
    if requested_user:
        return user_schema.jsonify(requested_user)
    return {"status": "not_found"}, 404


@app.route('/api/user/<uid>/posts', methods=["GET"])
@validate_token
def api_posts_get(uid, user_from_token):
    own = False
    if int(uid) == user_from_token.id:
        own = True
    if own:
        posts = Post.query.filter(Post.author_id == int(uid)).all()
    else:
        posts = Post.query.filter(Post.author_id == int(uid), Post.archived == False).all()
    return posts_schema.jsonify(posts), 200


# -----------------------------------POSTs Routes------------------------------------------


@app.route('/api/post/<pid>', methods=["GET"])
@validate_token
def api_post_get(pid, user_from_token):
    post = Post.query.filter(Post.id == int(pid)).first()
    if post:
        return post_schema.jsonify(post)
    return jsonify({"status": "not_found"}), 404


@app.route("/api/post/create", methods=["POST"])
@validate_token
def api_post_create(user_from_token):
    try:
        request_data = request.json
        if request_data["title"] and user_from_token:
            post = Post(title=request_data["title"], description=request_data["description"],
                        author=user_from_token)
            db.session.add(post)
            db.session.flush()
            print(post)
        # if post:
        # hashed_password = generate_password_hash(user.password, method="sha256")
        # user.password = hashed_password
        # db.session.add(user)
        # db.session.commit()
        # token = jwt.encode(
        #     {"user_id": user.id,
        #      "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30)},
        #     app.config["SECRET_KEY"]
        # )
            return {"post": post_schema.dump(post)}, 200
    except ValidationError as v:
        print(v)
        return jsonify({"message": "bad_request"}), 400
    except Exception as e:
        print("Exception", e)
        return jsonify({"message": "internal_server_error"}), 500
