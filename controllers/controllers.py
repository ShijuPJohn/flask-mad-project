from flask import render_template

from app import app


@app.route('/')
@app.route('/login')
def login_get():  # put controllers's code here
    return render_template('login.html')


@app.route('/signup')
def signup_get():  # put controllers's code here
    return render_template('signup.html')