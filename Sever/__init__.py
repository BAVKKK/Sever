from flask import Flask, session, current_app, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
import functools
import datetime
import logging


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
app.secret_key = '+91yyrL/v/+P45IPhHl7ACgQfD24enrXij0uUJRVucU='
app.config['JWT_SECRET_KEY'] = '654531c5ee6550c5bd6947b75bb25e4efe10d947a8d9520f1fa02ea7133fffd2'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://dba:24082001@localhost/sever'
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