from flask import current_app, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token
from datetime import timedelta

from Sever.utils import log_request, add_commit
from Sever.models import Users

def login(login, password):
    try: 
        user = Users.query.filter_by(login=login).first()  # Проверка пользователя
        if user and check_password_hash(user.hash_pwd, password):
            # Генерация JWT токена
            additional_claims = {
                "role_id": user.role_id,
                "id": user.id
            }
            expires = timedelta(hours=24) 
            access_token = create_access_token(identity=login, additional_claims=additional_claims, expires_delta=expires)
            response = {
                "access_token": access_token,
                "ROLE": user.role_id 
            }
            return jsonify(response), 200
        else:
            raise ValueError("Invalid login or password")
    except ValueError as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 401
    except Exception as ex:
        raise RuntimeError(f"Error during login: {ex}")

@log_request
def register(data):
    try:
        login = data['LOGIN']
        password = data['PASSWORD']
        
        # Проверка на существование пользователя с таким же логином
        if Users.query.filter_by(login=login).first():
            raise ValueError("User already exists")
        
        # Генерация хэша пароля
        hashed_password = generate_password_hash(password)
        
        # Создание нового пользователя
        new_user = Users(login=login,
                         hash_pwd=hashed_password,
                         email=data["EMAIL"],
                         role_id=data["ROLE_ID"],
                         phone=data["PHONE"])
        add_commit(new_user)

        return jsonify({"msg": "User registered successfully"}), 201
    except ValueError as ex:
        current_app.logger.warning(f"Registration failed: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 409
    except Exception as ex:
        current_app.logger.critical(f"Unknown error in register: {ex}")
        raise RuntimeError(f"Error during registration: {ex}")
