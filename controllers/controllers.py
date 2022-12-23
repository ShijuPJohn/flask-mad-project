import os

from flask import render_template, redirect
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from wtforms import StringField, EmailField, PasswordField, FileField
from wtforms.validators import InputRequired, Length

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
                              render_kw={"placeholder": "Description"})
    imageUrl = FileField()


@app.route('/', methods=["GET"])
def index_get():
    if current_user.is_authenticated:
        return redirect("/dashboard")
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
        image = form.imageUrl.data
        s_filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], s_filename))
        post = Post(title=form.title.data,
                    description=form.description.data,
                    imageUrl=image.filename,
                    author=current_user.id
                    )
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
    ownposts = Post.query.filter(Post.author == uid)
    followees_posts = []
    followees = User.query.filter(User.id == uid).first().follows
    print(followees)
    print(ownposts)
    return render_template("feed.html", user=current_user, posts=ownposts)


@app.route('/search', methods=["GET"])
@login_required
def search_get():
    users = User.query.all()
    return render_template("search.html", users=users)


@app.route('/test1', methods=["GET"])
def test1_get():
    shiju = User.query.filter(User.id == 1).first()
    jake = User.query.filter(User.id == 2).first()
    shiju.follows.append(jake)
    db.session.add(shiju)
    db.session.commit()
    print(shiju.follows)
    return "Hello"


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


@app.route('/test', methods=["GET"])
def testroute_get():
    print(current_user.follows)
    return "<h1>Test Route Success</h1>"
