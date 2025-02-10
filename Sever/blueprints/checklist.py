from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt

import json

from Sever.db_utils import fill_zeros, DescError, db_create_checklist
from Sever.models import *
from Sever.constants import *

checklist_bp = Blueprint('checklist', __name__, url_prefix='/checklist')

@checklist_bp.route('/create', methods=['POST'])
def create():
    try:
        json_data = request.get_json()  # {"CHECKLIST_ID": 1, "VALUES": [{"ID": 1}]}

        # Проверка, есть ли CHECKLIST_ID и корректный ли он
        cl_id = json_data.get("CHECKLIST_ID", 0)

        if cl_id == 0:
            cl_id = db_create_checklist()
        else:
            cl = Checklist.query.filter_by(id=cl_id).first()
            if cl is None:
                return jsonify({"STATUS": "Error", "message": f"Checklist with ID {cl_id} does not exist"}), 400

            # Если чеклист существует, удаляем все записи из ChecklistData для этого чеклиста
            ChecklistData.query.filter_by(checklist_id=cl_id).delete()

        # Проверка наличия VALUES
        values = json_data.get("VALUES", [])
        if not values:
            Checklist.query.filter_by(id=cl_id).delete()
            db.session.commit()
            return jsonify({"STATUS": "Warning", "message": "VALUES list is empty. Checklist has deleted."}), 200

        # Оптимизированная проверка Description
        desc_ids = [i.get("ID") for i in values]
        existing_descs = {desc.id for desc in Description.query.filter(Description.id.in_(desc_ids)).all()}

        for i in values:
            id = i.get("ID")
            if id not in existing_descs:
                raise DescError(f"""Description with ID {id} does not exist""")
            cld = ChecklistData.query.filter_by(description_id=id).first()
            if cld is not None and cld.checklist_id != cl_id:
                raise DescError(f"""Description with ID {id} is already in ChecklistData""")
            elif cld is None:  # Если запись не найдена, создаем новую
                new_checklist_data = ChecklistData(
                    checklist_id=cl_id,
                    description_id=id
                )
                db.session.add(new_checklist_data)

        db.session.commit()
        return jsonify({"STATUS": "Success", "ID": cl_id}), 200

    except DescError as ex:
        # Удаление чеклиста и связанных данных при ошибке
        ChecklistData.query.filter_by(checklist_id=cl_id).delete()
        Checklist.query.filter_by(id=cl_id).delete()
        db.session.commit()
        return jsonify({"STATUS": "Error", "message": str(ex)}), 400

    except Exception as ex:
        db.session.rollback()  # Откатываем транзакцию в случае ошибки
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

@checklist_bp.route('/get', methods=['GET'])
@jwt_required()
def get():
    try:
        claims = get_jwt()
        user_id = claims.get("id")  

        # Запрос в базу данных
        query_result = db.session.query(
            ChecklistData.checklist_id,
            Description.id,
            Description.name,
            Description.memo_id,
            Description.count,
            StatusOfPurchase.name,
            Description.contract_type,
            Units.short_name,
            Units.full_name
        ).join(Checklist, Checklist.id == ChecklistData.checklist_id
        ).join(Description, Description.id == ChecklistData.description_id
        ).join(Units, Units.id == Description.unit_id
        ).join(StatusOfPurchase, StatusOfPurchase.id == Description.status_id
        ).filter(Description.id_of_executor == user_id).all()

        # Группируем данные по CHECKLIST_ID
        checklist_data = {}
        checklist_info = {}
        for checklist_id, description_id, description_name, memo_id, count, status_name, contract_type, unit_short_name, unit_full_name in query_result:
            if checklist_id not in checklist_data:
                checklist_data[checklist_id] = []
                checklist_info[checklist_id] = {"STATUS": status_name, "CONTRACT_TYPE": contract_type}
            
            checklist_data[checklist_id].append({
                "ID": description_id,
                "NAME": description_name,
                "MEMO_ID": fill_zeros(memo_id),
                "COUNT": count,
                "UNIT_SHORT_NAME": unit_short_name,
                "UNIT_FULL_NAME": unit_full_name,
            })

        # Формируем список всех чек-листов
        response = [
            {
                "CHECKLIST_ID": cl_id,
                "STATUS": checklist_info[cl_id]["STATUS"],
                "CONTRACT_TYPE": ConstantSOP.CONTRACT_TYPE_REVERSE[checklist_info[cl_id]["CONTRACT_TYPE"]],
                "VALUES": values
            }
            for cl_id, values in checklist_data.items()
        ]

        json_response = json.dumps(response, ensure_ascii=False, indent=4)
        return Response(json_response, content_type='application/json; charset=utf-8')

    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

@checklist_bp.route('/delete', methods=['DELETE'])
def delete():
    try:
        cl_id = request.args.get("id")
        
        if not cl_id:
            return jsonify({"msg": "Checklist id is missing"}), 400

        # Выполняем запрос для получения данных
        cld = db.session.query(
            ChecklistData.id,
            Description.status_id,
            Description.contract_type
        ).join(
            Description, Description.id == ChecklistData.description_id
        ).filter(
            ChecklistData.checklist_id == cl_id
        ).first()

        if cld:
            if cld.status_id == ConstantSOP.NOT_SETTED or \
               cld.status_id in ConstantSOP.CONTRACT_RULES[cld.contract_type] and \
               cld.status_id == ConstantSOP.CONTRACT_RULES[cld.contract_type][0]:
                # Удаляем данные
                ChecklistData.query.filter_by(checklist_id=cl_id).delete()
                Checklist.query.filter_by(id=cl_id).delete()
                db.session.commit()
                return jsonify({"msg": "Checklist deleted successfully"}), 200
            else:
                return jsonify({"msg": "Pozdnyak metatsya"}), 200
        else:
            return jsonify({"msg": "Checklist not found"}), 404
            
    except Exception as ex:
        db.session.rollback()
        app.logger.error(f"Error deleting checklist with id {cl_id}: {str(ex)}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500


