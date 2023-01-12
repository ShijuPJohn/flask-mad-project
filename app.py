import os

from flask import Flask, render_template, send_from_directory

from config.config import ProductionConfig, LocalDevelopmentConfig
from models.models import db
from flask_swagger_ui import get_swaggerui_blueprint


def create_app():
    app = Flask(__name__, template_folder="templates")
    if os.getenv('ENV', "development") == "production":
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(LocalDevelopmentConfig)
    app.config['UPLOADS_DIR'] = 'static/uploads/'
    db.init_app(app)
    app.app_context().push()
    return app


app = create_app()
app.config["SECRET_KEY"] = "THIS_IS_MY_SUPER_SECRET"

db.create_all()
from controllers.controllers import *
from controllers.api_controllers import *

SWAGGER_URL = "/swagger"
API_URL = "/static/swagger.yaml"
SWAGGER_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        "app_name": "GeeksNetwork API"
    }
)
app.register_blueprint(SWAGGER_BLUEPRINT, url_prefix=SWAGGER_URL)



if __name__ == '__main__':
    app.run(debug=True)
