from flask import current_app, request
import functools
import logging

from Sever.extensions import db

def log_request(func):
    """
    Декоратор для логирования
    """
    @functools.wraps(func)
    def decorated_function(*args, **kwargs):
        current_app.logger.info('Request: %s %s', request.method, request.url)
        return func(*args, **kwargs)
    return decorated_function

def add_commit(param):
    """
    Сокращение для SQLAlchemy
    """
    db.session.add(param)
    db.session.commit()    