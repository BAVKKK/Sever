"""Функции для получения селекторов"""
from flask import jsonify, Response
import json
from Sever import app, db
from Sever.models import *


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
        responce = []
        sops = StatusOfPurchase.query.all()
        for sop in sops:
            data = {
                "ID": sop.id,
                "NAME": sop.name,
                "COEF": sop.coef
            }
            responce.append(data)

        return {"STATUS_OF_PURCHASE": responce}
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
