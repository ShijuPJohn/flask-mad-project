from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
@app.route('/login')
def login_get():  # put application's code here
    return render_template('login.html')


@app.route('/signup')
def signup_get():  # put application's code here
    return render_template('signup.html')


if __name__ == '__main__':
    app.run(debug=True)
