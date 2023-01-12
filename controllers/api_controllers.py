import datetime
import os

import jwt
from flask import request, jsonify
from flask_marshmallow import Marshmallow
from marshmallow import post_load, ValidationError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from app import app
from models.models import User, db, Post, Comment

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
        fields = ("id", "title", "description", "imageUrl", "time_created", "author", "archived")

    author = ma.Nested(UserDisplaySchema)


class PostCreateSchema(ma.Schema):
    class Meta:
        model = Post
        fields = ("title", "description", "author_id")

    @post_load
    def make_post(self, data, **kwargs):
        return Post(**data)


class CommentDisplaySchema(ma.Schema):
    class Meta:
        model = Comment
        fields = ("id", "comment", "author_id", "post_id")


user_schema = UserSchema()
user_signup_schema = UserSignupSchema()
user_display_schema = UserDisplaySchema()
users_display_schema = UserDisplaySchema(many=True)
post_schema = PostSchema()
posts_schema = PostSchema(many=True)
post_create_schema = PostCreateSchema()
comment_display_schema = CommentDisplaySchema()


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
@app.route("/api/user/users", methods=["GET"])
def api_users_get():
    try:
        users = User.query.all()
        return users_display_schema.dump(users), 200
    except Exception as e:
        print(e)
        return jsonify({"message": "error"}), 500


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
        return {"message": "unauthorized"}, 401

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


@app.route("/api/user/update-profile-pic", methods=["PUT"])
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
            return jsonify({"message": "login_success", "token": token}), 200
        return {"message": "invalid_credentials"}, 400
    return {"message": "invalid_data"}, 400


@app.route('/api/user/<uid>', methods=["GET"])
@validate_token
def api_user_get(uid, user_from_token):
    requested_user = User.query.filter(User.id == int(uid)).first()
    if requested_user:
        return users_display_schema.jsonify(requested_user)
    return {"status": "not_found"}, 404


@app.route('/api/user/follow-unfollow/<uid>', methods=["POST"])
@validate_token
def api_user_follow_unfollow(uid, user_from_token):
    try:
        user_to_follow_or_unfollow = User.query.filter(User.id == uid).first()
        if user_to_follow_or_unfollow:
            if user_to_follow_or_unfollow in user_from_token.follows:
                user_from_token.follows.remove(user_to_follow_or_unfollow)
                db.session.add(user_from_token)
                db.session.commit()
                return {"message": "unfollowed"}, 200
            else:
                user_from_token.follows.append(user_to_follow_or_unfollow)
                db.session.add(user_from_token)
                db.session.commit()
                return {"status": "followed"}
        return {"status": "not_found"}, 404
    except Exception as e:
        print(e)
        return {"message": "error"}, 500


# -----------------------------------POSTs Routes------------------------------------------


@app.route("/api/post/create", methods=["POST"])
@validate_token
def api_post_create(user_from_token):
    try:
        request_data = request.json
        request_data["author_id"] = user_from_token.id
        post_object_from_request = post_create_schema.load(request_data)
        db.session.add(post_object_from_request)
        db.session.commit()
        return {"post": post_schema.dump(post_object_from_request)}, 200

    except ValidationError as v:
        print(v)
        return jsonify({"message": "bad_request"}), 400
    except Exception as e:
        print("Exception", e)
        return jsonify({"message": "internal_server_error"}), 500


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


@app.route('/api/post/<pid>', methods=["GET"])
@validate_token
def api_post_get(pid, user_from_token):
    post = Post.query.filter(Post.id == int(pid)).first()
    if post:
        return post_schema.jsonify(post)
    return jsonify({"status": "not_found"}), 404


@app.route("/api/post/update-pic/<pid>", methods=["PUT"])
@validate_token
def api_post_update_pic(pid, user_from_token):
    try:
        post = Post.query.filter(Post.id == int(pid)).first()
        if post.author == user_from_token:
            file = request.files["file"]
            file_ext = file.filename[file.filename.rfind('.'):]
            s_fname = secure_filename(pid + file_ext)
            file.save(os.path.join(app.config['UPLOADS_DIR'] + "post_thumbs", s_fname))
            post.imageUrl = os.path.join(app.config['UPLOADS_DIR'] + "post_thumbs", s_fname)
            db.session.add(post)
            db.session.commit()
            return jsonify({"message": "file_saved"})
        return jsonify({"message": "unauthorized"})
    except Exception as e:
        print(e)
        return jsonify({"message": "bad_request"}), 400


@app.route("/api/post/<pid>/update", methods=["PUT"])
@validate_token
def api_post_update(pid, user_from_token):
    try:
        data_from_request = request.json
        if data_from_request["title"] and data_from_request["description"]:
            post = Post.query.filter(Post.id == int(pid)).first()
            post.title = data_from_request["title"]
            post.description = data_from_request["description"]
            db.session.add(post)
            db.session.commit()
            return {"message": "post_updated", "post": post_schema.dump(post)}, 201
        return jsonify({"message": "bad_request"}), 400
    except Exception as e:
        print(e)
        return {"message": "error"}, 500


@app.route("/api/post/<pid>/delete", methods=["DELETE"])
@validate_token
def api_post_delete(pid, user_from_token):
    try:
        post = Post.query.filter(Post.id == int(pid)).first()
        if post:
            if post.author == user_from_token:
                db.session.delete(post)
                db.session.commit()
                return {"message": "post_deleted"}, 200
            return {"message": "unauthorized"}, 400
        return {"message": "not_found"}, 404
    except Exception as e:
        print(e)
        return {"message": "error"}, 500


@app.route("/api/post/<pid>/like", methods=["POST"])
@validate_token
def api_post_like(pid, user_from_token):
    try:
        post = Post.query.filter(Post.id == int(pid)).first()
        if post and not post.archived:
            if user_from_token in post.liked_users:
                post.liked_users.remove(user_from_token)
                db.session.add(post)
                db.session.commit()
                return {"message": "unliked", "count": len(post.liked_users)}, 200
            else:
                post.liked_users.append(user_from_token)
                db.session.add(post)
                db.session.commit()
                return {"message": "liked", "count": len(post.liked_users)}, 200
        return {"message": "not_found"}, 404
    except Exception as e:
        print(e)
        return {"message": "error"}, 500


# ----------------------------Comment Routes----------------------------------

@app.route("/api/post/<pid>/comment", methods=["POST"])
@validate_token
def api_comment_create(pid, user_from_token):
    try:
        data_from_request = request.json
        if not data_from_request["comment"]:
            return {"message": "bad_request"}, 400
        post = Post.query.filter(Post.id == int(pid)).first()
        if post:
            comment = Comment(comment=data_from_request["comment"], author_id=user_from_token.id, post_id=int(pid))
            db.session.add(comment)
            db.session.commit()
            return {"message": "comment_posted", "comment": comment_display_schema.dump(comment)}, 201
        return {"message": "not_found"}, 404
    except Exception as e:
        return {"message": "error"}, 500


@app.route("/api/comment/delete/<cid>", methods=["DELETE"])
@validate_token
def api_comment_delete(cid, user_from_token):
    try:
        comment = Comment.query.filter(Comment.id == int(cid)).first()
        if not comment:
            return {"message": "not_found"}, 404
        if not comment.author == user_from_token and not comment.Post.author == user_from_token:
            return {"message": "unauthorized"}, 401
        db.session.delete(comment)
        db.session.commit()
        return {"message": "comment_deleted"}, 200
    except Exception as e:
        print(e)
        return {"message": "error"}, 500


@app.route("/api/comment/<cid>/like", methods=["POST"])
@validate_token
def api_comment_like(cid, user_from_token):
    try:
        comment = Comment.query.filter(Comment.id == int(cid)).first()
        if comment:
            if user_from_token in comment.liked_users:
                comment.liked_users.remove(user_from_token)
                db.session.add(comment)
                db.session.commit()
                return {"message": "unliked", "count": len(comment.liked_users)}, 200
            else:
                comment.liked_users.append(user_from_token)
                db.session.add(comment)
                db.session.commit()
                return {"message": "liked", "count": len(comment.liked_users)}, 200
        return {"message": "not_found"}, 404
    except Exception as e:
        print(e)
        return {"message": "error"}, 500


@app.route("/api/comment/<cid>/update", methods=["PUT"])
@validate_token
def api_comment_update(cid, user_from_token):
    try:
        data_from_request = request.json
        if data_from_request["comment"]:
            comment = Comment.query.filter(Comment.id == int(cid)).first()
            if comment.author == user_from_token:
                comment.comment = data_from_request["comment"]
                db.session.add(comment)
                db.session.commit()
                return {"message": "comment_updated", "comment": comment_display_schema.dump(comment)}, 201
            return jsonify({"message": "unauthorized"}), 401
        return jsonify({"message": "bad_request"}), 400
    except Exception as e:
        print(e)
        return {"message": "error"}, 500
