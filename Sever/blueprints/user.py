from flask import current_app, Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt

from Sever.utils import log_request
from Sever.utils.user import get_users_info, get_user_info

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/get_users', methods=['GET'])
@jwt_required()
@log_request
def get_users():
    try:
        filters = request.args.get("filters")
        return get_users_info(filters=filters)

    except ValueError as ex:
        current_app.logger.warning(f"Error in get_users (Incorrect data): {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 400

    except RuntimeError as ex:
        current_app.logger.error(f"Error in get_users (Execution error): {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

    except Exception as ex:
        current_app.logger.critical(f"Unknown error in get_users: {ex}")
        return jsonify({"STATUS": "Error", "message": "Internal server error"}), 500


@user_bp.route('/get_info', methods=['GET'])
@jwt_required()
@log_request
def get_info():
    try:
        claims = get_jwt()  # Получение дополнительных данных из токена
        role_id = claims.get("role_id")
        user_id = claims.get("id")

        if not role_id or not user_id:
            current_app.logger.warning("Error in get_info: incorrect token data")
            return jsonify({"STATUS": "Error", "message": "Invalid token data"}), 401

        return get_user_info(role_id=role_id, user_id=user_id)

    except ValueError as ex:
        current_app.logger.warning(f"Error in get_info (Incorrect data): {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 400

    except RuntimeError as ex:
        current_app.logger.error(f"Error in get_info (Execution error): {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500
        
    except Exception as ex:
        current_app.logger.critical(f"Unknown error in get_info: {ex}")
        return jsonify({"STATUS": "Error", "message": "Internal server error"}), 500
