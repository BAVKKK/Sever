from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
manager = LoginManager()
jwt = JWTManager()