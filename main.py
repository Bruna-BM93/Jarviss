from flask import Flask
from flask_migrate import Migrate
from db import db
from routes.user import user_blueprint
from routes.ai import ai_blueprint
from routes.calendar import calendar_blueprint
from routes.whatsapp import whatsapp_blueprint
import os

def create_app(config_object='config.DevelopmentConfig'):
    app = Flask(__name__)
    app.config.from_object(config_object)
    db.init_app(app)
    migrate = Migrate(app, db)

    with app.app_context():
        db.create_all()

    app.register_blueprint(user_blueprint, url_prefix='/users')
    app.register_blueprint(ai_blueprint, url_prefix='/ai')
    app.register_blueprint(calendar_blueprint, url_prefix='/calendar')
    app.register_blueprint(whatsapp_blueprint, url_prefix='/whatsapp')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run()
