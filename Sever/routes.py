# from flask import render_template, redirect, url_for, request, flash, session, jsonify, Response
# from werkzeug.security import check_password_hash, generate_password_hash
# from flask_jwt_extended import create_access_token, jwt_required
# from flask_jwt_extended import get_jwt
# from sqlalchemy import text, func, or_
# from sqlalchemy.orm import joinedload, aliased
# from collections import namedtuple, defaultdict
# import requests
# import json
# from datetime import datetime as dt

# from Sever.db.minio_lib import *

# from Sever import db, log_request
# from Sever.models import *
# from Sever.selector import *
# from Sever.db_utils import *
# from Sever.db.utils import *
# from Sever.constants import *

# # Исправить add_description
# # Подумать над костылем в add_memo

# # Добавить удаление мемо при ошибке в дескрипшен

# @app.route('/', methods=['GET', 'POST'])
# def main():
#     emp = Employees.query.filter_by().first()
#     data = {"SURNAME": emp.surname,
#             "NAME": emp.name,
#             "PATRONYMIC": emp.patronymic
#     }
#     return jsonify(data)

# #===================================================================================#
# #-----------------------------------РЕЕСТР------------------------------------------#
# #===================================================================================#

# #===================================================================================#
# #------------------------------ПОЛЬЗОВАТЕЛЬСКИЕ ДАННЫЕ------------------------------#
# #===================================================================================#

# #===================================================================================#
# #--------------------------------БЛОК С СЕЛЕКТОРАМИ---------------------------------#
# #===================================================================================#
 
# #===================================================================================#
# #--------------------------------РАБОТА С СОДЕРЖАНИЕМ-------------------------------#
# #===================================================================================#

# @app.route('/fill_his_test', methods=['GET'])
# def fill_his_test():
#     descs = Description.query.all()
#     for desc in descs:
#         for i in range (1, desc.status_id+1):
#             create_his(desc.id, i)
#     return jsonify({"STATUS": "Ok", "message": "Ok"}), 200

# @app.route('/save_file', methods=['POST'])
# def test_save():
#     try:
#         data = request.get_json()
#         memo_id = request.args.get("memo_id")
#         folder = request.args.get("folder")
#         save_file(memo_id, data, folder)

#         if memo_id is not None:
#             memo_id == remove_leading_zeros(memo_id)
#         else:
#             return jsonify({"msg": "memo id is missing"}), 400

#         return jsonify({"STATUS": "Ok"}), 200
#     except Exception as ex:
#         return jsonify({"STATUS": "Error", "message": str(ex)}), 500

