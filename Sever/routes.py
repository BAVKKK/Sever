from flask import render_template, redirect, url_for, request, flash, session, jsonify, Response
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_jwt_extended import get_jwt
from sqlalchemy import text, func, or_
from sqlalchemy.orm import joinedload
from collections import namedtuple
import requests
import json
from datetime import datetime as dt
from datetime import timedelta

from Sever.db.minio_lib import *

from Sever import app, db, log_request
from Sever.models import *
from Sever.selector import *
from Sever.db_utils import *
from Sever.db.utils import *
from Sever.constants import *

# Исправить add_description
# Подумать над костылем в add_memo


@app.route('/', methods=['GET', 'POST'])
def main():
    emp = Employees.query.filter_by().first()
    data = {"SURNAME": emp.surname,
            "NAME": emp.name,
            "PATRONYMIC": emp.patronymic
    }
    return jsonify(data)


@app.route('/form_memo', methods=['GET', 'POST'])
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

#===================================================================================#
#-----------------------------------РЕЕСТР------------------------------------------#
#===================================================================================#

def apply_reestr_filters(query, filters):
    try:
        if 'DESCRIPTION' in filters:
            filt = filters["DESCRIPTION"]
            query = query.filter(Memo.description.ilike(f"%{filt}%"))
        if 'INFO' in filters:
            filt = filters["INFO"]
            query = query.filter(Memo.info.ilike(f"%{filt}%"))
        if 'ITEM_NAME' in filters:
            filt = filters["ITEM_NAME"]
            query = query.join(Description).filter(Description.name.ilike(f"%{filt}%"))
        if 'EXECUTOR_NAME' in filters:
            filt = filters["EXECUTOR_NAME"]
            query = query.join(Description).join(Employees) \
                         .filter(
                             or_(
                                 Employees.name.ilike(f"%{filt}%"),
                                 Employees.surname.ilike(f"%{filt}%"),
                                 Employees.patronymic.ilike(f"%{filt}%")
                             )
                         )
        return query
    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

@app.route('/get_reestr', methods=['GET'])
@jwt_required()
def get_reestr():
    """
    Получить реестр
    """
    try:
        # Получение данных пользователя из токена
        claims = get_jwt()  # Получаем дополнительные данные из токена
        user_id = claims.get("id")
        role_id = claims.get("role_id")

        # Получаем код статуса из запроса
        status_id = request.args.get("status")

        # Получаем фильтры из запроса
        filters = request.args.get("filters")
        if filters:
            filters = json.loads(filters)

        user = Employees.query.filter_by(id=user_id).first()
        statuses = []
        # Определяем базовый запрос
        query = Memo.query

        # Определяем фильтрацию по ролям
        if role_id == 1:
            # Для роли "Руководитель отдела" (role_id == 1)
            department_id = user.department_id  # Получаем department_id руководителя
            statuses = [1, 2, 3, 4, 5, 6]
            query = query.filter(Memo.id_of_creator.in_(
                db.session.query(Employees.id).filter_by(department_id=department_id)
            ))
        elif role_id in [2, 3]:  # Если пользователь из групп 2 или 3
            # Получаем все заявки из таблицы memo
            statuses = [2, 4, 5, 6]
            pass  # Для всех заявок фильтры не применяются
        elif role_id == 4:  # Если пользователь из группы 4
            # Получаем заявки, где user.id либо в id_executor, либо в id_creator
            statuses = [1, 2, 3, 4, 5, 6]
            query = query.filter(
                (Memo.id_of_executor == user_id) | (Memo.id_of_creator == user_id)
            )
        elif role_id == 5:  # Если пользователь из группы 5
            # Получаем только те заявки, где пользователь указан в id_executor
            statuses = [2, 4, 5, 6]
            query = query.filter(Memo.id_of_executor == user_id)
        else:
            return jsonify({"msg": "Unauthorized role"}), 403

        # Применяем фильтр по статусу, если передан
        if status_id is not None:
            if int(status_id) in statuses:
                query = query.filter(Memo.status_id == status_id)
            else:
                msg = f"Incorrect status_id ({status_id}) for this role. Current role_id is {role_id}. Available statuses is {statuses}"
                return jsonify({"STATUS": "Error", "message": msg}), 400
        else:
            query = query.filter(Memo.status_id.in_(statuses))

        # Применяем фильтры, если они переданы
        if filters:
            query = apply_reestr_filters(query, filters)

        # Выполняем запрос
        memos = query.all()
        
        # Формируем ответ с нужными данными
        response = []
        for memo in memos:
            creator_id = memo.id_of_creator
            creator = Employees.query.filter_by(id=creator_id).first()
            department = Department.query.filter_by(id=creator.department_id).first()
            data = {
                "NAME": memo.info,
                "ID": fill_zeros(memo.id),
                "STATUS_ID": memo.status_id,
                "STATUS_TEXT": StatusOfExecution.query.filter_by(id=memo.status_id).first().name,
                "CREATOR_DEPARTMENT": department.name if department else "",
                "DATE_OF_CREATION": memo.date_of_creation.strftime("%Y-%m-%d")
            }
            response.append(data)

        json_response = json.dumps(response, ensure_ascii=False, indent=4)
        return Response(json_response, content_type='application/json; charset=utf-8')

    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

@app.route('/accept_memo', methods=['GET'])
@jwt_required()
def accept_memo():
    """
    Метод для принятия или отклонения служебной записки.
    Если передан аргумент 'accept' с значением отличным от нуля, то заявка принята, иначе отклонена
    """
    try:
        # Получение данных пользователя из токена
        claims = get_jwt()  # Получаем дополнительные данные из токена
        role_id = claims.get("role_id")

        if role_id == ConstantRolesID.DEPARTMENT_CHEF_ID:
            memo_id = request.args.get("id")
            status = request.args.get("accept")

            if memo_id is not None:
                memo_id == remove_leading_zeros(memo_id)
            else:
                return jsonify({"msg": "memo id is missing"}), 400

            memo = Memo.query.filter_by(id = memo_id).first()
            memo.status_id = ConstantSOE.REGISTERED if status else ConstantSOE.DECLINE_BY_DEP_CHEF # Зарегистрировна, Отклонена нач. отдела
            add_commit(memo)
        elif role_id == ConstantRolesID.MTO_CHEF_ID:
            memo_id = request.args.get("id")
            status = request.args.get("accept")

            if memo_id is not None:
                memo_id == remove_leading_zeros(memo_id)
            else:
                return jsonify({"msg": "memo id is missing"}), 400

            memo = Memo.query.filter_by(id = memo_id).first()
            memo.status_id = ConstantSOE.EXECUTION if status else ConstantSOE.DECLINE_BY_MTO_CHEF # Исполнение, Отклонена отделом закупок
            add_commit(memo)
        else:
            return jsonify({"msg": "Unauthorized role"}), 403

        return jsonify({"STATUS": "Ok", "message": "Success"}), 200
    
    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

#===================================================================================#
#------------------------------ПОЛЬЗОВАТЕЛЬСКИЕ ДАННЫЕ------------------------------#
#===================================================================================#
def apply_users_filters(query, filters):
    try:
        if 'FIO' in filters:
            filt = filters["FIO"]
            full_name_expression = func.concat(Employees.surname, ' ', Employees.name, ' ', Employees.patronymic)
            query = query.filter(full_name_expression.ilike(f'%{filt}%'))
        if 'ROLE' in filters:
            filt = filters["ROLE"]
            query = query.filter(Users.role_id == filt)
        return query
    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

@app.route('/get_users', methods=['GET'])
@jwt_required()
def get_users_info():
    try:
        filters = request.args.get("filters")
          
        query = db.session.query(Employees, Users).outerjoin(
            Users, Employees.id == Users.id
        )
        if filters:
            filters = json.loads(filters)
            query = apply_users_filters(query, filters)
        employees = query.order_by(Employees.department_id).all()
        departments = Department.query.order_by(Department.id).all()
        response = {}
        added_users = set()  # Множество для отслеживания уже добавленных пользователей

        for dep in departments:
            response[dep.id] = {"NAME": dep.name,
                                "EMPLOYEES": []}
            for emp, user in employees:
                if emp.id not in added_users:
                    if dep.id == emp.department_id:
                        data = {
                            "ID": emp.id,
                            "SURNAME": emp.surname,
                            "NAME": emp.name,
                            "PATRONYMIC": emp.patronymic,
                            "POST": emp.post,
                            "PHONE": user.phone if user else "",
                            "EMAIL": user.email if user else ""
                        }
                        response[dep.id]["EMPLOYEES"].append(data)
                        added_users.add(emp.id)  # Добавляем пользователя в множество
                    elif dep.id != emp.department_id:
                        break
                else:
                    pass
        # Фильтруем отделы, в которых нет сотрудников
        filtered_response = {dep_id: dep_data for dep_id, dep_data in response.items() if dep_data["EMPLOYEES"]}
        json_response = json.dumps(filtered_response, ensure_ascii=False, indent=4)
        return Response(json_response, content_type='application/json; charset=utf-8')
        
    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

@app.route('/get_user_info', methods=['GET'])
@jwt_required()
def get_user_info():
    try:
        claims = get_jwt()  # Получение дополнительных данных из токена
        role_id = claims.get("role_id")
        user_id = claims.get("id")
        user = Employees.query.filter_by(id = user_id).first()
        role = Roles.query.filter_by(id = role_id).first()

        if user:
            dep = Department.query.filter_by(id = user.department_id).first()
            data = {
                "ID": user.id,
                "SURNAME": user.surname,
                "NAME": user.name,
                "PATRONYMIC": user.patronymic,
                "POST": user.post,
                "ROLE":
                {
                    "ID": role_id,
                    "NAME": role.name,
                    "COMMENT": role.comment
                },
                "DEPARTMENT":
                {
                    "ID": user.department_id,
                    "NAME": dep.name
                }
            }
            json_response = json.dumps(data, ensure_ascii=False, indent=4)
            return Response(json_response, content_type='application/json; charset=utf-8')
        return jsonify({"msg": "User not found"}), 404
    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    login = data.get('LOGIN')
    password = data.get('PASSWORD')
    
    if not login or not password:
        return jsonify({"msg": "Login and password are required"}), 400
    
    # Проверка пользователя
    user = Users.query.filter_by(login=login).first()
    if user and check_password_hash(user.hash_pwd, password):
        # Генерация JWT токена
        additional_claims = {
            "role_id": user.role_id,
            "id": user.id
        }
        expires = timedelta(hours=24) 
        access_token = create_access_token(identity=login, additional_claims=additional_claims, expires_delta=expires)
        response = {
            "access_token": access_token,
            "ROLE": user.role_id 
        }
        return jsonify(response), 200
    else:
        return jsonify({"msg": "Invalid login or password"}), 401
    
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        if not data or 'LOGIN' not in data or 'PASSWORD' not in data:
            return jsonify({"msg": "Login and password are required"}), 400
        
        login = data['LOGIN']
        password = data['PASSWORD']
        
        # Проверка на существование пользователя с таким же логином
        if Users.query.filter_by(login=login).first():
            return jsonify({"msg": "User already exists"}), 409
        
        # Генерация хэша пароля
        hashed_password = generate_password_hash(password)
        
        # Создание нового пользователя
        new_user = Users(login=login,
                         hash_pwd=hashed_password,
                         email = data["EMAIL"],
                         role_id = data["ROLE_ID"],
                         phone = data["PHONE"])
        add_commit(new_user)

        return jsonify({"msg": "User registered successfully"}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "An error occurred", "error": str(e)}), 500

#===================================================================================#
#--------------------------------БЛОК С СЕЛЕКТОРАМИ---------------------------------#
#===================================================================================#

@app.route('/get_selectors', methods=['GET'])
def get_selectors():
    """
    Вызов функции Sever.selector.get_all_selectors() для получения всех редкоизменяемых вспомогательных списков из бд.
    """
    return get_all_selectors()
    
#===================================================================================#
#--------------------------------РАБОТА С СОДЕРЖАНИЕМ-------------------------------#
#===================================================================================#

@app.route('/set_sop', methods=['POST'])
def set_sop():
    try:
        id = request.args.get("id")
        if id:
            desc = Description.query.filter_by(id = id).first()
            desc.status_id += 1
            add_commit(desc)
            his = HistoryOfchangingSOP.query.filter_by(description_id = id).first()
            create_his(desc.id , desc.status_id)
            return jsonify({"STATUS": "Ok", "message": f"{id} status of purchase changed successfully"}), 200
        else:
            return jsonify({"STATUS": "Error", "message": "The \'id\' argument is not set"}), 400
    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500
    
@app.route('/get_aggregate', methods=['GET'])
@jwt_required()
def aggregate_description_data():
    """
    Хз че это но я что-то да написал
    Вроде считает количество всех предметов, да ещё и по статусам
    """
    try:
        # Получение данных пользователя из токена
        claims = get_jwt()  # Получение дополнительных данных из токена
        role_id = claims.get("role_id")
        user_id = claims.get("id")

        # Получение параметра status из запроса
        status = request.args.get("status")

        # Определяем базовый запрос
        query = db.session.query(
            Description.name,
            func.sum(Description.count).label('total_count'),
            Units.short_name.label('short_name'),
            Units.full_name.label('full_name')
        ).join(
            Units, Description.unit_id == Units.id
        )

        # Применяем фильтр по status_id, если параметр status передан
        if status is not None:
            count = db.session.query(func.count(StatusOfPurchase.id)).scalar()
            if int(status) > 0 and int(status) <= count:
                query = query.filter(Description.status_id == status)
            else:
                return jsonify({"STATUS": "Error", "message": "Unknown status"}), 400

        # Группируем данные
        query = query.group_by(
            Description.name,
            Units.short_name,
            Units.full_name
        )

        # Фильтрация данных в зависимости от роли
        if role_id == 2:
            # Роль 2 видит всю агрегацию
            pass
        elif role_id == 5:
            # Роль 5 видит только те записи, где он указан в id_of_executor
            query = query.filter(Description.id_of_executor == user_id)
        else:
            return jsonify({"STATUS": "Error", "message": "Unauthorized role"}), 403

        # Выполняем запрос
        aggregated_data = query.all()

        # Преобразуем результат в список словарей
        result = [
            {
                "NAME": row.name,
                "TOTAL_COUNT": row.total_count,
                "SHORT_NAME": row.short_name,
                "FULL_NAME": row.full_name
            }
            for row in aggregated_data
        ]

        json_response = json.dumps(result, ensure_ascii=False, indent=4)
        return Response(json_response, content_type='application/json; charset=utf-8')
    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500


@app.route('/fill_his_test', methods=['GET'])
def fill_his_test():
    descs = Description.query.all()
    for desc in descs:
        for i in range (1, desc.status_id+1):
            create_his(desc.id, i)
    return jsonify({"STATUS": "Ok", "message": "Ok"}), 200

@app.route('/save_file', methods=['POST'])
def test_save():
    try:
        data = request.get_json()
        memo_id = request.args.get("memo_id")
        folder = request.args.get("folder")
        save_file(memo_id, data, folder)

        if memo_id is not None:
            memo_id == remove_leading_zeros(memo_id)
        else:
            return jsonify({"msg": "memo id is missing"}), 400

        return jsonify({"STATUS": "Ok"}), 200
    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

@app.route('/count_memo', methods=['GET'])
def count_memo():
    try:
        mode = request.args.get("mode")
        if mode == "status":
            response = count_memo_by_status()
        elif mode == "executor":
            response = count_memo_by_executor()
        else:
            response = {"msg": "Please chose a mode like a param. Use '?mode=status' or '?mode=executor'."}
        json_response = json.dumps(response, ensure_ascii=False, indent=4)
        return Response(json_response, content_type='application/json; charset=utf-8')
    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

@app.route('/get_kanban', methods=['GET'])
@jwt_required()
def get_kanban():
    try:
        # Получение данных пользователя из токена
        claims = get_jwt()  # Получаем дополнительные данные из токена
        user_id = claims.get("id")

        # Запрос с явным соединением и загрузкой связанных данных
        kanbans = (
            Kanban.query
            .join(KanbanColumn, Kanban.column_id == KanbanColumn.id)
            .filter(Kanban.user_id == user_id)
            .options(joinedload(Kanban.kanban_column))  # Загружаем связанные данные
            .all()
        )
        # Формирование ответа
        response = []
        for kanban in kanbans:
            data = {
                "ID": kanban.id,
                "COLUMN": kanban.kanban_column.name,  # Доступ к имени столбца
                "COLUMNID": kanban.column_id,
                "CONTENT": kanban.info
            }
            response.append(data)

        # Возвращаем JSON-ответ
        json_response = json.dumps(response, ensure_ascii=False, indent=4)
        return Response(json_response, content_type='application/json; charset=utf-8')
    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

@app.route('/set_kanban', methods=['POST'])
@jwt_required()
def set_kanban():
    try:
        # Получение данных пользователя из токена
        claims = get_jwt()  # Получаем дополнительные данные из токена
        user_id = claims.get("id")

        json_data = request.get_json()

        kanbans = Kanban.query.filter_by(user_id = user_id).delete()
        db.session.commit()
        for i in json_data:
            new_kanban = Kanban(
                user_id = int(user_id),
                column_id = int(i["COLUMNID"]),
                info = i["CONTENT"]
            )
            add_commit(new_kanban)
        
        return jsonify({"STATUS": "Ok"}), 200
    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500
