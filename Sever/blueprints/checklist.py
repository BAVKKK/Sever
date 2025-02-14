from flask import current_app, Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt

import json

from Sever.constants import ConstantRolesID
from Sever.utils import log_request
from Sever.models import Users
from Sever.utils.checklist import create as ut_create, get as ut_get, delete as ut_delete, add_contract_file

checklist_bp = Blueprint('checklist', __name__, url_prefix='/checklist')

@checklist_bp.route('/create', methods=['POST'])
@jwt_required()
@log_request
def create():
    try:
        claims = get_jwt()
        user_id = claims.get("id")
        role_id = claims.get("role_id")

        if role_id != ConstantRolesID.MTO_EMPLOYEE_ID:
            raise PermissionError("Only MTO employee can create checklist")
        
        json_data = request.get_json()  # {"CHECKLIST_ID": 1, "VALUES": [{"ID": 1}]}

        # Проверка, есть ли CHECKLIST_ID и корректный ли он
        cl_id = json_data.get("CHECKLIST_ID", 0)

        return ut_create(json_data=json_data, cl_id=cl_id, user_id=user_id)

    except ValueError as ex:
        current_app.logger.warning(f"ValueError in create checklist: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 400

    except TypeError as ex:
        current_app.logger.warning(f"TypeError in create checklist: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 400
    
    except PermissionError as ex:
        current_app.logger.warning(f"PermissionError in create checklist: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 403

    except RuntimeError as ex:
        current_app.logger.error(f"RuntimeError in create checklist: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

    except Exception as ex:
        current_app.logger.critical(f"Unknown error in create checklist: {ex}")
        return jsonify({"STATUS": "Error", "message": "Internal server error"}), 500


@checklist_bp.route('/get', methods=['GET'])
@jwt_required()
def get():
    try:
        claims = get_jwt()
        user_id = claims.get("id")
        if user_id and Users.query.filter_by(id=user_id).first():
            return ut_get(user_id)
        else:
            return jsonify({"STATUS": "Error", "message": "Unauthorized role"}), 403

    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500


@checklist_bp.route('/delete', methods=['DELETE'])
@jwt_required()
@log_request
def delete():
    try:
        claims = get_jwt()
        user_id = claims.get("id")
        role_id = claims.get("role_id")

        if role_id != ConstantRolesID.MTO_EMPLOYEE_ID:
            raise PermissionError("Only MTO employee can create checklist")
            
        cl_id = request.args.get("id")
        
        if not cl_id:
            return jsonify({"msg": "Checklist id is missing"}), 400
        else:
            return ut_delete(cl_id)
    
    except ValueError as ex:
        current_app.logger.warning(f"ValueError in create checklist: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 400

    except TypeError as ex:
        current_app.logger.warning(f"TypeError in create checklist: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 400
    
    except PermissionError as ex:
        current_app.logger.warning(f"PermissionError in create checklist: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 403

    except RuntimeError as ex:
        current_app.logger.error(f"RuntimeError in create checklist: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

    except Exception as ex:
        current_app.logger.critical(f"Unknown error in create checklist: {ex}")
        return jsonify({"STATUS": "Error", "message": "Internal server error"}), 500


@checklist_bp.route('/save_contract', methods=['POST'])
@jwt_required()
@log_request
def save_contract():
    try:
        claims = get_jwt()
        role_id = claims.get("role_id")

        if role_id != ConstantRolesID.MTO_EMPLOYEE_ID:
            raise PermissionError("Only MTO employee can add contracts")
            
        data = request.get_json()
        
        if not data:
            return jsonify({"msg": "Data is missing"}), 400
        else:
            return add_contract_file(data)
    
    except ValueError as ex:
        current_app.logger.warning(f"ValueError in add contracts: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 400

    except TypeError as ex:
        current_app.logger.warning(f"TypeError in add contracts: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 400
    
    except PermissionError as ex:
        current_app.logger.warning(f"PermissionError in add contracts: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 403

    except RuntimeError as ex:
        current_app.logger.error(f"RuntimeError in add contracts: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

    except Exception as ex:
        current_app.logger.critical(f"Unknown error in add contracts: {ex}")
        return jsonify({"STATUS": "Error", "message": "Internal server error"}), 500