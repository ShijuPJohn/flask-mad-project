import os

from flask import render_template, redirect, request
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from wtforms import StringField, EmailField, PasswordField, FileField, BooleanField
from wtforms.validators import InputRequired, Length
from wtforms.widgets import TextArea

from app import app
from models.models import User, db, Post, Comment

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
            filename = image.filename
            f_extension = filename[filename.rfind('.') + 1:]
            s_filename = secure_filename(str(new_user.id) + '.' + f_extension)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'] + "user_thumbs", s_filename))
            new_user.imageUrl = app.config['UPLOAD_FOLDER'] + "user_thumbs/" + s_filename
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
            filename = image.filename
            f_extension = filename[filename.rfind('.') + 1:]
            s_filename = secure_filename(str(post.id) + '.' + f_extension)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'] + "post_thumbs", s_filename))
            post.imageUrl = app.config['UPLOAD_FOLDER'] + "post_thumbs/" + s_filename
            db.session.add(post)
        db.session.commit()

        return render_template("message.html", message_title="Post Created",
                               message_body="New Post Created",
                               message_action_link=f"/post/{post.id}",
                               message_action_message="See Post"
                               )
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
    print(posts)
    return render_template("feed.html", user=current_user, posts=posts)


@app.route('/feed', methods=["GET"])
@login_required
def feed_get():
    uid = current_user.id
    followees = current_user.follows
    followees_ids = [i.id for i in followees]
    followees_ids.append(uid)
    posts_display = Post.query.filter(Post.author_id.in_(followees_ids)).all()
    time_obj = {}
    for post in posts_display:
        time_obj[post.id] = post.time_created.strftime("%d-%B-%Y, %I:%M %p")

    return render_template("feed.html", posts=posts_display, time_obj=time_obj)


# @app.route('/search', methods=["GET"])
# @login_required
# def search_get():
#     users = User.query.filter(User.id != current_user.id).all()
#     return render_template("search.html", users=users)


@app.route('/search', methods=["GET"])
@login_required
def search_post():
    if request.args:
        name = request.args["name"]
        users = User.query.filter(User.username.startswith(name), User.id != current_user.id).all()
        return render_template("search.html", users=users)
    users = User.query.filter(User.id != current_user.id).all()
    return render_template("search.html", users=users)


@app.route('/follow-unfollow/<uid>', methods=["GET"])
@login_required
def follow_unfollow_get(uid):
    required_user = User.query.filter(User.id == uid).first()
    if required_user in current_user.follows:
        current_user.follows.remove(required_user)
        db.session.add(current_user)
        db.session.commit()
        return render_template("message.html", message_title="Unfollowed",
                               message_body="Unfollowed the user",
                               message_action_link="/search",
                               message_action_message="Search Users"
                               )
    else:
        print("else part worked")
        current_user.follows.append(required_user)
        db.session.add(current_user)
        db.session.commit()
        return render_template("message.html", message_title="Followed",
                               message_body="Followed the user",
                               message_action_link="/search",
                               message_action_message="Search Users"
                               )


@app.route('/users/<followers_followees>', methods=["GET"])
@login_required
def users_get(followers_followees):
    if followers_followees == "followers":
        users = current_user.followers
    elif followers_followees == "followees":
        users = current_user.follows
    else:
        return render_template("not_found.html")
    return render_template("users.html", users=users)


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
    for post in current_user.posts:
        time_obj[post.id] = post.time_created.strftime("%d-%B-%Y, %I:%M %p")
    return render_template("all-posts.html", time_obj=time_obj)


@app.route('/delete-post/<pid>', methods=["GET"])
@login_required
def delete_post_get(pid):
    post = Post.query.filter(Post.id == pid).first()
    if post:
        if post.author_id == current_user.id:
            Post.query.filter(Post.id == pid).delete()
            db.session.commit()
            return render_template("message.html", message_title="Delete Successful",
                                   message_body="Post deleted successfully",
                                   message_action_link="/all-posts",
                                   message_action_message="Go back"
                                   )
        return render_template("message.html", message_title="Not Authorized",
                               message_body="You can't delete other user's posts",
                               message_action_link="/all-posts",
                               message_action_message="Go back"
                               )
    return render_template("message.html", message_title="Not Found",
                           message_body="No posts found with this ID",
                           message_action_link="/all-posts",
                           message_action_message="Go back"
                           )


@app.route('/post/<pid>', methods=["GET"])
@login_required
def post_details_get(pid):
    post = Post.query.filter(Post.id == int(pid)).first()
    time = post.time_created.strftime("%d-%B-%Y, %I:%M %p")
    form = CommentForm()
    comment_time_obj = {}
    for comment in post.comments:
        comment_time_obj[comment.id] = comment.time_created.strftime("%d-%B-%Y, %I:%M %p")
    return render_template("post_details.html", post=post, time=time, form=form, comment_time_obj=comment_time_obj)


@app.route('/like_dislike_post/<pid>', methods=["GET"])
@login_required
def like_post_get(pid):
    post = Post.query.filter(Post.id == int(pid)).first()
    if current_user in post.liked_users:
        post.liked_users.remove(current_user)
        db.session.add(post)
        db.session.commit()
        return render_template("message.html", message_title="Unliked",
                               message_body="Unliked the post",
                               message_action_link=f"/post/{post.id}",
                               message_action_message="See Post"
                               )
    else:
        post.liked_users.append(current_user)
        db.session.add(post)
        db.session.commit()
        return render_template("message.html", message_title="Liked",
                               message_body="Liked the post",
                               message_action_link=f"/post/{post.id}",
                               message_action_message="See Post"
                               )


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


@app.route('/comment-like-unlike/<cid>', methods=["GET"])
@login_required
def comment_likeunlike_get(cid):
    comment = Comment.query.filter(Comment.id == int(cid)).first()
    if current_user in comment.liked_users:
        comment.liked_users.remove(current_user)
        db.session.add(comment)
        db.session.commit()
        return render_template("message.html", message_title="Comment Liked",
                               message_body="Liked the comment",
                               message_action_link=f"/post/{comment.post_id}",
                               message_action_message="See Post"
                               )
    else:
        comment.liked_users.append(current_user)
        db.session.add(comment)
        db.session.commit()
        return render_template("message.html", message_title="Comment Unliked",
                               message_body="Unliked the comment",
                               message_action_link=f"/post/{comment.post_id}",
                               message_action_message="See Post"
                               )


@app.route('/comment-delete/<cid>', methods=["GET"])
@login_required
def comment_delete_get(cid):
    comment = Comment.query.filter(Comment.id == int(cid)).first()
    if comment.author == current_user:
        comment.liked_users = []
        Comment.query.filter(Comment.id == int(cid)).delete()
        db.session.commit()
        return render_template("message.html", message_title="Comment Deleted",
                               message_body="Deleted the comment",
                               message_action_link=f"/post/{comment.post_id}",
                               message_action_message="See Post")
    else:
        return render_template("message.html", message_title="Can't Delete",
                               message_body="Cannot delete the comment",
                               message_action_link=f"/post/{comment.post_id}",
                               message_action_message="See Post")


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
                filename = image.filename
                f_extension = filename[filename.rfind('.') + 1:]
                s_filename = secure_filename(str(post.id) + '.' + f_extension)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'] + "post_thumbs", s_filename))
                post.imageUrl = app.config['UPLOAD_FOLDER'] + "post_thumbs/" + s_filename
            if not form.is_same_image.data and not form.imageUrl.data:
                post.imageUrl = app.config['UPLOAD_FOLDER'] + "post_thumbs/default_post.png"
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
            filename = image.filename
            f_extension = filename[filename.rfind('.') + 1:]
            s_filename = secure_filename(str(current_user.id) + '.' + f_extension)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'] + "user_thumbs", s_filename))
            current_user.imageUrl = app.config['UPLOAD_FOLDER'] + "user_thumbs/" + s_filename
        if not form.is_same_image.data and not form.imageUrl.data:
            user.imageUrl = app.config['UPLOAD_FOLDER'] + "user_thumbs/pro_img1.png"
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
