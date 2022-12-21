from flask import render_template, redirect
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, EmailField, PasswordField
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


class PostForm(FlaskForm):
    title = StringField("title", validators=[InputRequired()],
                        render_kw={"placeholder": "Title"})
    description = StringField("description", validators=[InputRequired(), Length(min=8)],
                              render_kw={"placeholder": "Description"})
    imageUrl = StringField("imageUrl",
                           render_kw={"placeholder": "Image URL"})
    authorName = StringField("authorName", validators=[InputRequired()],
                             render_kw={"placeholder": "Image URL"})


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
    print("Method called")
    form = LoginForm()
    print(form)
    if form.validate_on_submit():
        user = User.query.filter(User.email == form.email.data).first()
        print(user)
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
        new_user = User(form.name.data, form.email.data, hashed_password)
        db.session.add(new_user)
        db.session.commit()
        print(new_user)
        return "<h1>" + "user created with id" + str(new_user.id) + "</h1>"
    return "<h1>Error</h1>"


@app.route('/logout', methods=["GET"])
@login_required
def logout_get():
    logout_user()
    return redirect("/login")
