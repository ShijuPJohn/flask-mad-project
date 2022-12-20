from flask import render_template
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash
from wtforms import StringField, EmailField, PasswordField
from wtforms.validators import InputRequired, Length

from app import app
from models.models import User, db


class LoginForm(FlaskForm):
    email = EmailField("username", validators=[InputRequired()])
    password = PasswordField("username", validators=[InputRequired(), Length(min=8, max=64)])


class SignupForm(FlaskForm):
    email = EmailField("email", validators=[InputRequired()], render_kw={"placeholder": "Email"})
    name = StringField("name", validators=[InputRequired(), Length(min=8, max=64)], render_kw={"placeholder": "Name"})
    password = PasswordField("password", validators=[InputRequired(), Length(min=8, max=100)],
                             render_kw={"placeholder": "Password"})


@app.route('/')
@app.route('/login')
def login_get():  # put controllers's code here
    return render_template('login.html')


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
