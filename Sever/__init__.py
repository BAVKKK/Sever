from flask import Flask
from flask_cors import CORS

import datetime
import logging

from Sever.configs.flask import SECRET_KEY, JWT_SECRET_KEY, SQLALCHEMY_DATABASE_URI
from Sever.extensions import db, manager, jwt

from Sever.blueprints import register_blueprints
    
def configure_logging(app):
    # Настройки логирования приложения
    app.logger.setLevel(logging.INFO)

    # Формат сообщений логов
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Обработчик логов для записи в файл
    file_handler = logging.FileHandler(f"Sever.log")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)

def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_AS_ASCII'] = False  # Отключает ASCII-кодирование
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True  # Делает вывод более читабельным
    app.permanent_session_lifetime = datetime.timedelta(days=1)
    CORS(app, supports_credentials=True)
    
    db.init_app(app)
    manager.init_app(app)
    jwt.init_app(app)

    configure_logging(app)

    register_blueprints(app) 
    return app

