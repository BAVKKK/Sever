from flask import current_app, Blueprint, request, jsonify
from Sever.utils import log_request
from Sever.utils.auth import login, register

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['POST'])
@log_request
def auth_login():
    try:
        data = request.get_json()
        login_value = data.get('LOGIN')
        password = data.get('PASSWORD')

        if not login_value or not password:
            return jsonify({"msg": "Login and password are required"}), 400

        return login(login_value, password)
    except ValueError as ex:
        current_app.logger.warning(f"Login failed: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 401
    except Exception as ex:
        current_app.logger.critical(f"Unknown error in login: {ex}")
        raise RuntimeError(f"Error during login: {ex}")

    
@auth_bp.route('/register', methods=['POST'])
@log_request
def auth_register():
    try:
        data = request.get_json()
        if not data or 'LOGIN' not in data or 'PASSWORD' not in data:
            return jsonify({"msg": "Login and password are required"}), 400

        return register(data)
    except ValueError as ex:
        current_app.logger.warning(f"Registration failed: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 409
    except Exception as ex:
        current_app.logger.critical(f"Unknown error in register: {ex}")
        return jsonify({"STATUS": "Error", "message": "Internal server error"}), 500
