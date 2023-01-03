import os

from flask import render_template, redirect, request
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from wtforms import StringField, EmailField, PasswordField, FileField
from wtforms.validators import InputRequired, Length
from wtforms.widgets import TextArea

from app import app
from models.models import User, db, Post

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
    password = PasswordField("password", validators=[InputRequired(), Length(min=8, max=100)],
                             render_kw={"placeholder": "Password"})
    imageUrl = FileField()


class PostForm(FlaskForm):
    title = StringField("title", validators=[InputRequired()],
                        render_kw={"placeholder": "Title"})
    description = StringField("description", validators=[InputRequired(), Length(min=8)],
                              render_kw={"placeholder": "Description"}, widget=TextArea())
    imageUrl = FileField()


class CommentForm(FlaskForm):
    pass


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
    user = current_user
    return render_template("dashboard.html", user=user)


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
            print(image)
            filename = image.filename
            f_extension = filename[filename.rfind('.') + 1:]
            s_filename = secure_filename(str(new_user.id) + '.' + f_extension)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'] + "user_thumbs", s_filename))
            new_user.imageUrl = app.config['UPLOAD_FOLDER'] + "user_thumbs/" + s_filename
            db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect("/dashboard")
    return "<h1>Error</h1>"


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

    return "<h1> Post created</h1>"


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
        return "<h1>Unfollowed</h1>"
    else:
        print("else part worked")
        current_user.follows.append(required_user)
        db.session.add(current_user)
        db.session.commit()
        return "<h1>followed</h1>"


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
    print(post)
    return render_template("post_details.html", post=post, time=time)


@app.route('/likepost/<pid>', methods=["GET"])
@login_required
def like_post_get(pid):
    post = Post.query.filter(Post.id == int(pid)).first()
    post.liked_users.append(current_user)
    db.session.add(post)
    db.session.commit()
    return "<h1>Liked Success</h1>"
