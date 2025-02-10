from flask import current_app, Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt

import json

from Sever.utils import log_request
from Sever.utils.reestr import get_reestr

reestr_bp = Blueprint('reestr', __name__, url_prefix='/reestr')

@reestr_bp.route('/get', methods=['GET'])
@jwt_required()
@log_request
def get():
    """
    Получить реестр
    """
    try:
        # Получение данных пользователя из токена
        claims = get_jwt()  # Получаем дополнительные данные из токена
        user_id = claims.get("id")
        role_id = claims.get("role_id")

        # Получаем код статуса из запроса
        status = request.args.get("status")

        # Получаем фильтры из запроса
        filters = request.args.get("filters")
        if filters:
            filters = json.loads(filters)

        return get_reestr(user_id=user_id, role_id=role_id, status=status, filters=filters)
    except ValueError as ex:
        current_app.logger.warning(f"ValueError in reestr: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 400

    except TypeError as ex:
        current_app.logger.warning(f"TypeError in reestr: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 400
    
    except PermissionError as ex:
        current_app.logger.warning(f"PermissionError in reestr: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 403

    except RuntimeError as ex:
        current_app.logger.error(f"RuntimeError in reestr: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

    except Exception as ex:
        current_app.logger.critical(f"Unknown error in reestr: {ex}")
        return jsonify({"STATUS": "Error", "message": "Internal server error"}), 500

