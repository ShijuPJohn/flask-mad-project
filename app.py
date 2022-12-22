import os

from flask import Flask, render_template

from config.config import ProductionConfig, LocalDevelopmentConfig
from models.models import db

UPLOAD_FOLDER = 'static/uploads/'


def create_app():
    app = Flask(__name__, template_folder="templates")
    if os.getenv('ENV', "development") == "production":
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(LocalDevelopmentConfig)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    db.init_app(app)
    app.app_context().push()
    return app


app = create_app()
app.config["SECRET_KEY"] = "THIS_IS_MY_SUPER_SECRET"

db.create_all()
from controllers.controllers import *

if __name__ == '__main__':
    app.run(debug=True)
