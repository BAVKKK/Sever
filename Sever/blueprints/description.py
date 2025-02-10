from flask import current_app, Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt

import json

from Sever.utils import log_request
from Sever.utils.description import set_contract_type, set_sop as set_sop_utils, aggregate_data

desc_bp = Blueprint('desc', __name__, url_prefix='/desc')

@desc_bp.route('/set_contract_type', methods=['POST'])
@log_request
def set_ct():
    try:
        ids = request.get_json()  # Получаем список ID из тела запроса

    except Exception as ex:
        current_app.logger.critical(f"The 'ids' argument is not set or is empty: {ex}")
        return jsonify({"STATUS": "Error", "message": "The 'ids' argument is not set or is empty"}), 400

    try:
        contract_type = request.args.get("type")
        
        if not contract_type or not ids:
            return jsonify({"STATUS": "Error", "message": "Missing required parameters"}), 400
     
        return set_contract_type(contract_type=contract_type, ids=ids)

    except ValueError as ex:
        current_app.logger.warning(f"Error in set_contract_type (Incorrect data): {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 400

    except RuntimeError as ex:
        current_app.logger.error(f"Error in set_contract_type (Execution error): {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

    except Exception as ex:
        current_app.logger.critical(f"Unknown error in set_contract_type: {ex}")
        return jsonify({"STATUS": "Error", "message": "Internal server error"}), 500


@desc_bp.route('/set_sop', methods=['POST'])
@log_request
def set_sop():
    try:
        ids = request.get_json()  # Получаем список ID из тела запроса

    except Exception as ex:
        current_app.logger.critical(f"The 'ids' argument is not set or is empty: {ex}")
        return jsonify({"STATUS": "Error", "message": "The 'ids' argument is not set or is empty"}), 400

    try:
        if not ids:
            return jsonify({"STATUS": "Error", "message": "The 'ids' argument is not set or is empty"}), 400

        if not isinstance(ids, list):
            return jsonify({"STATUS": "Error", "message": "The 'ids' argument must be a list"}), 400

        # Проверка, что все ID являются целыми числами
        for id in ids:
            if not isinstance(id, int):
                return jsonify({"STATUS": "Error", "message": "All 'id' values must be integers"}), 400

        # Вызов внутренней функции, которая будет обрабатывать список id
        return set_sop_utils(ids=ids)

    except ValueError as ex:
        current_app.logger.warning(f"ValueError in set_sop: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 400

    except TypeError as ex:
        current_app.logger.warning(f"TypeError in set_sop: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 400

    except RuntimeError as ex:
        current_app.logger.error(f"RuntimeError in set_sop: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

    except Exception as ex:
        current_app.logger.critical(f"Unknown error in set_sop: {ex}")
        return jsonify({"STATUS": "Error", "message": "Internal server error"}), 500


@desc_bp.route('/get_aggregate', methods=['GET'])
@jwt_required()
@log_request
def aggregate_description_data():
    """
    Агрегация данных по memo_id и name с учетом ролей и статуса memo.
    """
    try:
        claims = get_jwt()
        role_id = claims.get("role_id")
        user_id = claims.get("id")

        status = request.args.get("status")

        return aggregate_data(role_id=role_id, user_id=user_id, status=status)

    except ValueError as ex:
        current_app.logger.warning(f"ValueError in get_aggregate: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 400

    except TypeError as ex:
        current_app.logger.warning(f"TypeError in get_aggregate: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 400
    
    except PermissionError as ex:
        current_app.logger.warning(f"PermissionError in get_aggregate: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 403

    except RuntimeError as ex:
        current_app.logger.error(f"RuntimeError in get_aggregate: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

    except Exception as ex:
        current_app.logger.critical(f"Unknown error in get_aggregate: {ex}")
        return jsonify({"STATUS": "Error", "message": "Internal server error"}), 500

