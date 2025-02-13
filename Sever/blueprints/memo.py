from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt

import json

from Sever.utils import log_request, add_commit
from Sever.db_utils import remove_leading_zeros, model_for_memo, add_memo, count_memo_by_executor, count_memo_by_status
from Sever.constants import *
from Sever.models import Memo

memo_bp = Blueprint('memo', __name__, url_prefix='/memo')

@memo_bp.route('/form', methods=['GET', 'POST'])
@jwt_required()
def form():
    """
    Метод для записи служебной записки в БД (POST)
    или
    Метод для получения служебной запиский из БД (GET)
    """
    try:
        if request.method == "POST":
            json_data = request.get_json()
            if not json_data:
                return jsonify({"STATUS": "Error", "message": "No data"}), 400
            else:
                err = add_memo(json_data)
                return err  # Из функции уже json приходит
        if request.method == "GET":
            id = request.args.get("id")
            if id is not None:
                id = remove_leading_zeros(id)
            return model_for_memo(id)
    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

@memo_bp.route('/accept', methods=['POST'])
@jwt_required()
def accept():
    """
    Метод для принятия или отклонения служебной записки.
    Если передан аргумент 'accept' с значением отличным от нуля, то заявка принята, иначе отклонена
    """
    try:
        # Получение данных пользователя из токена
        claims = get_jwt()  # Получаем дополнительные данные из токена
        role_id = claims.get("role_id")

        json_data = request.get_json()

        if role_id == ConstantRolesID.DEPARTMENT_CHEF_ID:
            memo_id = request.args.get("id")
            status = request.args.get("accept")

            if memo_id is not None:
                memo_id = remove_leading_zeros(memo_id)
            else:
                return jsonify({"msg": "memo id is missing"}), 400

            memo = Memo.query.filter_by(id = memo_id).first()
            memo.status_id = ConstantSOE.REGISTERED if int(status) else ConstantSOE.DECLINE_BY_DEP_CHEF # Зарегистрировна, Отклонена нач. отдела
            
            memo.head_comment = json_data.get("COMMENT","")
            add_commit(memo)
        elif role_id == ConstantRolesID.MTO_CHEF_ID:
            memo_id = request.args.get("id")
            status = request.args.get("accept")

            if memo_id is not None:
                memo_id = remove_leading_zeros(memo_id)
            else:
                return jsonify({"msg": "memo id is missing"}), 400

            memo = Memo.query.filter_by(id = memo_id).first()
            memo.status_id = ConstantSOE.EXECUTION if int(status) else ConstantSOE.DECLINE_BY_MTO_CHEF # Исполнение, Отклонена отделом закупок

            memo.executor_comment = json_data.get("COMMENT","")
            add_commit(memo)
        else:
            return jsonify({"msg": "Unauthorized role"}), 403

        return jsonify({"STATUS": "Ok", "message": "Success"}), 200
    
    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

@memo_bp.route('/count', methods=['GET'])
@jwt_required()
def count():
    """
    Метод для подсчета служебных записок по фильтрам.
    """
    try:
        mode = request.args.get("mode")
        if mode == "status": # Подсчет служебных записок по статусам исполения 
            response = count_memo_by_status()
        elif mode == "executor": # Подсчет служебных записок по исполнителям
            response = count_memo_by_executor()
        else:
            response = {"msg": "Please chose a mode like a param. Use '?mode=status' or '?mode=executor'."}
        json_response = json.dumps(response, ensure_ascii=False, indent=4)
        return Response(json_response, content_type='application/json; charset=utf-8')
    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500