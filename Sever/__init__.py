from flask import Flask, session, current_app, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
import functools
import datetime
import logging

from Sever.configs.flask import SECRET_KEY, JWT_SECRET_KEY, SQLALCHEMY_DATABASE_URI


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

def log_request(func):
    """
    Декоратор для логирования
    """
    @functools.wraps(func)
    def decorated_function(*args, **kwargs):
        current_app.logger.info('Request: %s %s', request.method, request.url)
        return func(*args, **kwargs)
    return decorated_function

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False  # Отключает ASCII-кодирование
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True  # Делает вывод более читабельным
app.permanent_session_lifetime = datetime.timedelta(days=1)
CORS(app, supports_credentials=True)
db = SQLAlchemy(app)
manager = LoginManager(app)
jwt = JWTManager(app)

configure_logging(app)

from Sever import models, routes




#db.create_all()