"""Функции для получения селекторов"""
from flask import jsonify, Response
import json
from Sever import db
from Sever.models import *
from Sever.constants import *

def get_units_list():
    try:
        responce = []
        units = Units.query.all()
        for unit in units:
            data = {
                "ID": unit.id,
                "SHORT_NAME": unit.short_name,
                "FULL_NAME": unit.full_name
            }
            responce.append(data)

        return {"UNITS": responce}
    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

def get_departments_list():
    try:
        responce = []
        departments = Department.query.all()
        for department in departments:
            data = {
                "ID": department.id,
                "NAME": department.name
            }
            responce.append(data)

        return {"DEPARTMENTS": responce}
    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

def get_sop_list():
    try:
        response = {"STATUS_OF_PURCHASE": {}}
        
        # Загружаем статусы закупок из БД в словарь с coef и coef2
        sops = {
            sop.id: {
                "ID": sop.id,
                "NAME": sop.name,
                "COEF": sop.coef,
                "COEF2": sop.coef2
            } for sop in StatusOfPurchase.query.all()
        }

        # Добавляем DEFAULT как первую запись
        if ConstantSOP.NOT_SETTED in sops:
            default_sop = sops[ConstantSOP.NOT_SETTED].copy()  # Создаем копию, чтобы не менять исходный словарь
            default_sop.pop("COEF2", None)  # Удаляем COEF2, если он есть
            response["STATUS_OF_PURCHASE"]["DEFAULT"] = default_sop

        # Формируем структуру согласно ConstantSOP.CONTRACT_RULES
        for contract_type, statuses in ConstantSOP.CONTRACT_RULES.items():
            response["STATUS_OF_PURCHASE"][contract_type] = [
                {
                    "ID": sops[s_id]["ID"],
                    "NAME": sops[s_id]["NAME"],
                    "COEF": sops[s_id]["COEF2"] if contract_type == ConstantSOP.CONTRACT_TYPE["Invoice-contract"] else sops[s_id]["COEF"]
                }
                for s_id in statuses if s_id in sops
            ]

        return response
    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

def get_soe_list():
    try:
        responce = []
        soes = StatusOfExecution.query.all()
        for soe in soes:
            data = {
                "ID": soe.id,
                "NAME": soe.name
            }
            responce.append(data)

        return {"STATUS_OF_EXECUTION": responce}
    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

def get_all_selectors():
    try:
        responce = {}
        responce.update(get_units_list())
        responce.update(get_departments_list())
        responce.update(get_soe_list())
        responce.update(get_sop_list())
        json_response = json.dumps(responce, ensure_ascii=False, indent=4)
        return Response(json_response, content_type='application/json; charset=utf-8')
            
    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500
