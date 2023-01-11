import datetime
import os
import time

import jwt
import werkzeug
from flask import render_template, redirect, request, jsonify
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from flask_marshmallow import Marshmallow
from flask_restful import reqparse
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from wtforms import StringField, EmailField, PasswordField, FileField, BooleanField
from wtforms.validators import InputRequired, Length
from wtforms.widgets import TextArea

from app import app
from models.models import User, db, Post, Comment

ma = Marshmallow(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_get"


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.id == user_id).first()


class LoginForm(FlaskForm):
    email = EmailField("username", validators=[InputRequired()])
    password = PasswordField("username", validators=[InputRequired(), Length(min=8, max=64)])


class SignupForm(FlaskForm):
    email = EmailField("email", validators=[InputRequired()], render_kw={"placeholder": "Email"})
    name = StringField("name", validators=[InputRequired(), Length(min=8, max=64)], render_kw={"placeholder": "Name"})
    password = PasswordField("password", validators=[InputRequired(), Length(min=8, max=64)])
    imageUrl = FileField()


class UserEditForm(FlaskForm):
    name = StringField("name", validators=[InputRequired(), Length(min=8, max=64)], render_kw={"placeholder": "Name"})
    password = PasswordField("password", validators=[InputRequired(), Length(min=8, max=100)],
                             render_kw={"placeholder": "Password"})
    is_same_image = BooleanField('Use the same post image?')
    imageUrl = FileField()


class PostForm(FlaskForm):
    title = StringField("title", validators=[InputRequired()],
                        render_kw={"placeholder": "Title"})
    description = StringField("description", validators=[InputRequired(), Length(min=8)],
                              render_kw={"placeholder": "Description"}, widget=TextArea())
    imageUrl = FileField()


class PostEditForm(FlaskForm):
    title = StringField("title", validators=[InputRequired()],
                        render_kw={"placeholder": "Title"})
    description = StringField("description", validators=[InputRequired(), Length(min=8)],
                              render_kw={"placeholder": "Description"}, widget=TextArea())
    is_same_image = BooleanField('Use the same post image?')
    imageUrl = FileField()


class CommentForm(FlaskForm):
    comment = StringField("comment", validators=[InputRequired()], render_kw={"placeholder": "Comment"},
                          widget=TextArea())


@app.route('/', methods=["GET"])
def index_get():
    if current_user.is_authenticated:
        return redirect("/feed")
    return redirect("/login")


@app.route('/login', methods=["GET"])
def login_get():
    form = LoginForm()
    return render_template('login.html', form=form)


@app.route('/login', methods=["POST"])
def login_post():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(User.email == form.email.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect("/dashboard")
    return render_template('login_error.html')


@app.route('/dashboard', methods=["GET"])
@login_required
def dashboard_get():
    return render_template("dashboard.html", user=current_user)


@app.route('/signup', methods=["GET"])
def signup_get():
    form = SignupForm()
    return render_template('signup.html', form=form)


@app.route('/signup', methods=["POST"])
def signup_post():
    form = SignupForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method="sha256")
        new_user = User(username=form.name.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.flush()
        if form.imageUrl.data:
            image = form.imageUrl.data
            file_ext = image.filename[image.filename.rfind('.'):]
            s_fname = secure_filename(str(new_user.id) + file_ext)
            image.save(os.path.join(app.config['UPLOADS_DIR'] + "user_thumbs", s_fname))
            new_user.imageUrl = app.config['UPLOADS_DIR'] + "user_thumbs/" + s_fname
            db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect("/dashboard")
    return render_template("message.html", message_title="Signup Error",
                           message_body="Data validation error",
                           message_action_link="/signup",
                           message_action_message="Go back"
                           )


@app.route('/logout', methods=["GET"])
@login_required
def logout_get():
    logout_user()
    return redirect("/login")


@app.route('/create-post', methods=["GET"])
@login_required
def create_post_get():
    form = PostForm()
    return render_template("create-post.html", form=form)


@app.route('/create-post', methods=["POST"])
@login_required
def create_post_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data,
                    description=form.description.data,
                    author=current_user
                    )
        db.session.add(post)
        db.session.flush()
        if form.imageUrl.data:
            image = form.imageUrl.data
            file_ext = image.filename[image.filename.rfind('.'):]
            s_fname = secure_filename(str(post.id) + file_ext)
            image.save(os.path.join(app.config['UPLOADS_DIR'] + "post_thumbs", s_fname))
            post.imageUrl = app.config['UPLOADS_DIR'] + "post_thumbs/" + s_fname
            db.session.add(post)
        db.session.commit()
        return redirect(f"/post/{post.id}")
    return render_template("message.html", message_title="Post Create Error",
                           message_body="Data Invalid",
                           message_action_link="/create-post",
                           message_action_message="Try again"
                           )


@app.route('/my-posts', methods=["GET"])
@login_required
def my_posts_get():
    uid = current_user.id
    posts = Post.query.filter(Post.author == uid)
    return render_template("feed.html", user=current_user, posts=posts)


@app.route('/feed', methods=["GET"])
@login_required
def feed_get():
    uid = current_user.id
    followees = current_user.follows
    followees_ids = [i.id for i in followees]
    followees_ids.append(uid)
    posts_display = Post.query.filter(Post.author_id.in_(followees_ids), Post.archived != True).order_by(
        Post.time_created.desc()).all()
    time_obj = {}
    for post in posts_display:
        now_timestamp = time.time()
        offset = datetime.datetime.fromtimestamp(now_timestamp) - datetime.datetime.utcfromtimestamp(now_timestamp)
        localtime = post.time_created + offset
        time_obj[post.id] = localtime.strftime("%d-%B-%Y, %I:%M %p")

    return render_template("feed.html", posts=posts_display, time_obj=time_obj)


@app.route('/search', methods=["GET"])
@login_required
def search_post():
    if request.args:
        name = request.args["name"]
        users = User.query.filter(User.username.startswith(name), User.id != current_user.id).all()
        return render_template("search.html", users=users)
    users = User.query.filter(User.id != current_user.id).all()
    return render_template("search.html", users=users)


@app.route('/follow-unfollow', methods=["POST"])
@login_required
def follow_unfollow_post():
    body_data = request.get_json()
    uid = body_data["userId"]
    user_to_follow = User.query.filter(User.id == int(uid)).first()
    if current_user == user_to_follow:
        return {"status": "invalid_operation"}
    if user_to_follow in current_user.follows:
        current_user.follows.remove(user_to_follow)
        db.session.add(current_user)
        db.session.commit()
        return {"status": "unfollowed", "followers_count": len(user_to_follow.followers)}
    else:
        current_user.follows.append(user_to_follow)
        db.session.add(current_user)
        db.session.commit()
        return {"status": "followed", "followers_count": len(user_to_follow.followers)}


@app.route('/users/<followers_followees>', methods=["GET"])
@login_required
def users_get(followers_followees):
    if followers_followees == "followers":
        users = current_user.followers
    elif followers_followees == "followees":
        users = current_user.follows
    else:
        return render_template("not_found.html")
    return render_template("users.html", users=users,
                           title="Your Followers" if followers_followees == "followers" else "Your followees")


@app.route('/user/<uid>', methods=["GET"])
@login_required
def user_get(uid):
    if int(uid) == current_user.id:
        return redirect("/dashboard")
    user = User.query.filter(User.id == uid).first()
    return render_template("user.html", user=user)


@app.route('/all-posts', methods=["GET"])
@login_required
def all_posts_get():
    time_obj = {}
    posts = current_user.posts
    for post in posts:
        now_timestamp = time.time()
        offset = datetime.datetime.fromtimestamp(now_timestamp) - datetime.datetime.utcfromtimestamp(now_timestamp)
        localtime = post.time_created + offset
        time_obj[post.id] = localtime.strftime("%d-%B-%Y, %I:%M %p")
    return render_template("all-posts.html", posts=posts, time_obj=time_obj)


@app.route('/delete-post/<pid>', methods=["DELETE"])
@login_required
def delete_post_get(pid):
    post = Post.query.filter(Post.id == pid).first()
    if post:
        if post.author_id == current_user.id:
            post = Post.query.filter(Post.id == pid).first()
            db.session.delete(post)
            db.session.commit()
            return {"status": "deleted"}
        return {"status": "unauthorized"}
    return {"status": "not_found"}


@app.route('/archive-post/<pid>', methods=["GET"])
@login_required
def archive_post_get(pid):
    post = Post.query.filter(Post.id == pid).first()
    if post:
        if post.author_id == current_user.id:
            if not post.archived:
                post.archived = True
                db.session.add(post)
                db.session.commit()
                return {"status": "archived"}
            else:
                post.archived = False
                db.session.add(post)
                db.session.commit()
                return {"status": "unarchived"}
        return {"status": "unauthorized"}
    return {"status": "not_found"}


@app.route('/post/<pid>', methods=["GET"])
@login_required
def post_details_get(pid):
    post = Post.query.filter(Post.id == int(pid)).first()
    now_timestamp = time.time()
    offset = datetime.datetime.fromtimestamp(now_timestamp) - datetime.datetime.utcfromtimestamp(now_timestamp)
    localtime = post.time_created + offset
    formatted_time = localtime.strftime("%d-%B-%Y, %I:%M %p")
    form = CommentForm()
    comment_time_obj = {}
    print(type(post.comments))
    if post.comments:
        for comment in post.comments:
            now_timestamp = time.time()
            offset = datetime.datetime.fromtimestamp(now_timestamp) - datetime.datetime.utcfromtimestamp(now_timestamp)
            comment_localtime = comment.time_created + offset
            comment_time_obj[comment.id] = comment_localtime.strftime("%d-%B-%Y, %I:%M %p")
    return render_template("post_details.html", post=post, time=formatted_time, form=form,
                           comment_time_obj=comment_time_obj)


@app.route('/like_dislike_post', methods=["POST"])
@login_required
def like_post_get2():
    body_data = request.get_json()
    pid = body_data["postID"]
    post = Post.query.filter(Post.id == int(pid)).first()
    if current_user in post.liked_users:
        post.liked_users.remove(current_user)
        db.session.add(post)
        db.session.commit()
        return {"message": "unliked", "count": len(post.liked_users)}
    else:
        post.liked_users.append(current_user)
        db.session.add(post)
        db.session.commit()
        return {"message": "liked", "count": len(post.liked_users)}


@app.route('/create_comment/<pid>', methods=["POST"])
@login_required
def create_comment_post(pid):
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(comment=form.comment.data, author_id=current_user.id, post_id=int(pid))
        db.session.add(comment)
        db.session.commit()
        return render_template("message.html", message_title="Comment Added",
                               message_body="Added the comment successfully",
                               message_action_link=f"/post/{pid}",
                               message_action_message="See Post"
                               )


@app.route('/create_comment2', methods=["POST"])
@login_required
def create_comment_post2():
    body_data = request.get_json()
    comment_body = body_data["commentBody"]
    pid = body_data["postID"]
    print(comment_body, pid)
    if len(comment_body) > 0:
        comment = Comment(comment=comment_body, author_id=current_user.id, post_id=int(pid))
        db.session.add(comment)
        db.session.commit()
        post = Post.query.filter(Post.id == pid).first()
        now_timestamp = time.time()
        offset = datetime.datetime.fromtimestamp(now_timestamp) - datetime.datetime.utcfromtimestamp(now_timestamp)
        comment_localtime = comment.time_created + offset
        comment_time_str = comment_localtime.strftime("%d-%B-%Y, %I:%M %p")
        return {"status": "created",
                "commentID": comment.id,
                "authorImageUrl": current_user.imageUrl,
                "count": len(post.comments),
                "commentLikesCount": len(comment.liked_users),
                "authorName": current_user.username,
                "time": comment_time_str
                }

    return {"status": "invalid_data"}


@app.route('/comment-like-unlike', methods=["POST"])
@login_required
def comment_likeunlike_get():
    body_data = request.get_json()
    cid = body_data["comment_id"]
    comment = Comment.query.filter(Comment.id == int(cid)).first()
    if current_user in comment.liked_users:
        comment.liked_users.remove(current_user)
        db.session.add(comment)
        db.session.commit()
        return {"message": "unliked", "count": len(comment.liked_users)}
    else:
        comment.liked_users.append(current_user)
        db.session.add(comment)
        db.session.commit()
        return {"message": "liked", "count": len(comment.liked_users)}


@app.route('/comment-delete/<cid>', methods=["DELETE"])
@login_required
def comment_delete_get(cid):
    comment = Comment.query.filter(Comment.id == int(cid)).first()
    if comment:
        post = comment.Post
        if comment.author == current_user or comment.Post.author == current_user:
            comment.liked_users = []
            Comment.query.filter(Comment.id == int(cid)).delete()
            db.session.commit()
            return {"status": "deleted", "count": len(post.comments)}
        else:
            return {"status": "unauthorized", "count": len(post.comments)}
    return {"status": "not_found"}


@app.route('/edit-post/<pid>', methods=["GET"])
@login_required
def edit_post_get(pid):
    post = Post.query.filter(Post.id == int(pid)).first()
    form = PostEditForm()
    form.title.data = post.title
    form.description.data = post.description
    if post.author == current_user:
        return render_template("edit_post.html", post=post, form=form)
    else:
        return render_template("message.html", message_title="Not authorized",
                               message_body="You're not authorized to edit this post",
                               message_action_link=f"/post/{pid}",
                               message_action_message="See Post")


@app.route('/edit-post/<pid>', methods=["POST"])
@login_required
def edit_post_post(pid):
    form = PostEditForm()
    post = Post.query.filter(Post.id == int(pid)).first()
    if post.author == current_user:
        if form.validate_on_submit():
            post.title = form.title.data
            post.description = form.description.data
            if not form.is_same_image.data and form.imageUrl.data:
                image = form.imageUrl.data
                file_ext = image.filename[image.filename.rfind('.'):]
                s_fname = secure_filename(str(post.id) + file_ext)
                image.save(os.path.join(app.config['UPLOADS_DIR'] + "post_thumbs", s_fname))
                post.imageUrl = app.config['UPLOADS_DIR'] + "post_thumbs/" + s_fname
            if not form.is_same_image.data and not form.imageUrl.data:
                post.imageUrl = app.config['UPLOADS_DIR'] + "post_thumbs/default_post.png"
            db.session.add(post)
            db.session.commit()
            return render_template("message.html", message_title="Update Success",
                                   message_body="Post updated successfully",
                                   message_action_link=f"/post/{pid}",
                                   message_action_message="See Post")
        else:
            return render_template("message.html", message_title="Update Error",
                                   message_body="Couldn't update post. Data validation error",
                                   message_action_link=f"/edit-post/{pid}",
                                   message_action_message="Try Again")
    else:
        return render_template("message.html", message_title="Not authorized",
                               message_body="You're not authorized to edit this post",
                               message_action_link=f"/post/{pid}",
                               message_action_message="See Post")


@app.route("/edit-user", methods=["GET"])
@login_required
def edit_user_get():
    form = UserEditForm()
    form.name.data = current_user.username
    return render_template("edit_user.html", form=form)


@app.route("/delete-user", methods=["DELETE"])
@login_required
def delete_user():
    user = User.query.filter(User.id == current_user.id).first()
    db.session.delete(user)
    db.session.commit()
    return {"status": "deleted"}


@app.route("/edit-user", methods=["POST"])
@login_required
def edit_user_post():
    form = UserEditForm()
    user = User.query.filter(User.id == current_user.id).first()
    if form.validate_on_submit():
        user.username = form.name.data
        hashed_password = generate_password_hash(form.password.data, method="sha256")
        user.password = hashed_password
        if not form.is_same_image.data and form.imageUrl.data:
            image = form.imageUrl.data
            file_ext = image.filename[image.filename.rfind('.'):]
            s_fname = secure_filename(str(current_user.id) + file_ext)
            image.save(os.path.join(app.config['UPLOADS_DIR'] + "user_thumbs", s_fname))
            current_user.imageUrl = app.config['UPLOADS_DIR'] + "user_thumbs/" + s_fname
        if not form.is_same_image.data and not form.imageUrl.data:
            user.imageUrl = app.config['UPLOADS_DIR'] + "user_thumbs/pro_img1.png"
        db.session.add(user)
        db.session.commit()
        return render_template("message.html", message_title="Update Success",
                               message_body="User details updated successfully",
                               message_action_link="/dashboard",
                               message_action_message="Go to dashboard")
    else:
        return render_template("message.html", message_title="Update Error",
                               message_body="Couldn't update user. Data validation error",
                               message_action_link="/edit-user",
                               message_action_message="Try again")


@app.route('/user/<uid>/followers', methods=["GET"])
@login_required
def user_followers_get(uid):
    user = User.query.filter(User.id == uid).first()
    users = user.followers
    return render_template("users.html", users=users, title=f"{user.username}'s Followers")


@app.route('/user/<uid>/followees', methods=["GET"])
@login_required
def user_followees_get(uid):
    user = User.query.filter(User.id == uid).first()
    print(user)
    print(user.follows)
    users = user.follows
    return render_template("users.html", users=users, title=f"{user.username}'s Followees")


@app.route('/user/<uid>/all-posts', methods=["GET"])
@login_required
def users_all_posts_get(uid):
    time_obj = {}
    user = User.query.filter(User.id == int(uid)).first()
    posts = list(filter(lambda x: not x.archived, list(user.posts)))
    print(posts)
    for post in posts:
        now_timestamp = time.time()
        offset = datetime.datetime.fromtimestamp(now_timestamp) - datetime.datetime.utcfromtimestamp(now_timestamp)
        localtime = post.time_created + offset
        time_obj[post.id] = localtime.strftime("%d-%B-%Y, %I:%M %p")
    return render_template("all-posts.html", posts=posts, time_obj=time_obj)
