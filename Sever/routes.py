from flask import render_template, redirect, url_for, request, flash, session, current_app, jsonify, Response
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_jwt_extended import get_jwt
from sqlalchemy import text, func
from collections import namedtuple
import requests
import json
import functools
from datetime import datetime as dt
from datetime import timedelta


from Sever import app, db
from Sever.models import *


# Подумать над костылем в add_memo


def log_request(func):
    """
    Декоратор для логирования
    
    """
    @functools.wraps(func)
    def decorated_function(*args, **kwargs):
        current_app.logger.info('Request: %s %s', request.method, request.url)
        return func(*args, **kwargs)
    return decorated_function

def add_commit(param):
    """
    Сокращение для SQLAlchemy
    """
    db.session.add(param)
    db.session.commit()    

def add_description(memo_id, data):
    try:
        # Удаляем все существующие записи к конкретной заявке
        Description.query.filter_by(memo_id=memo_id).delete()
        db.session.commit()
        
        # Добавляем новые записи
        for disc in data:
            date_of_delivery = None
            executor_id = None
            if disc.get("DATE_OF_DELIVERY"):
                try:
                    date_of_delivery = dt.strptime(disc["DATE_OF_DELIVERY"], "%Y-%m-%d").date()
                except ValueError:
                    raise ValueError(f"Invalid date format: {disc['DATE_OF_DELIVERY']}")
            if disc.get("EXECUTOR"):
                executor_id = disc["EXECUTOR"]["ID"]
            
            new_disc = Description(
                memo_id=memo_id,
                pos=disc.get("POSITION"),
                name=disc.get("NAME"),
                count=disc.get("COUNT", 0),
                contract=disc.get("CONTRACT"),
                unit_id=disc.get("UNIT_CODE"),
                status_id=disc.get("STATUS_CODE"),
                date_of_delivery=date_of_delivery,
                id_of_executor = executor_id
            )
            db.session.add(new_disc)
        
        db.session.commit()
        return jsonify({"STATUS": "Success", "message": "Descriptions added successfully"}), 200
    
    except Exception as ex:
        db.session.rollback()
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

@log_request
def add_memo(data):
    """
    Метод для добавления служебной записки
    """
    try:
        if data["ID_MEMO"] == 0: # Создаем новую запись в таблицу служебок
            memo = Memo(
                date_of_creation = dt.now().date(),
                info = data["INFO"],
                id_of_creator = data["CREATOR"]["ID"]
            )
            add_commit(memo)
        else:
            memo = Memo.query.filter_by(id=data["ID_MEMO"]).first()

        # Добавление или обновление данных в служебках
        date_of_appointment = dt.strptime(data["DATE_OF_APPOINTMENT"], "%Y-%m-%d").date() if data["DATE_OF_APPOINTMENT"] else None
        memo.info = data["INFO"]
        # Пока не работает, т.к. всегда ответственный начальник второго отдела, а именно 7
        #memo.id_of_executor = data["EXECUTOR"]["ID"] if data["EXECUTOR"]["ID"] is not None and data["EXECUTOR"]["ID"] != 0 else None
        memo.id_of_executor = Users.query.filter_by(role_id = 2).first().id # Подставляем актуальное ID руководителя 13 отдела
        memo.date_of_appointment = date_of_appointment

        memo.description = data["JUSTIFICATION"]
        memo.status_id = data["STATUS_CODE"] if data["STATUS_CODE"] and data["STATUS_CODE"] != 0 else 1
        add_commit(memo)
        err = add_description(memo.id, data["DESCRIPTION"])
        current_app.logger.info({"STATUS": "Success", "ID": memo.id})
        return jsonify({"STATUS": "Success", "ID": memo.id}), 200

    except Exception as ex:
        current_app.logger.info(ex)
        db.session.rollback()
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500
        
    
def model_for_memo(id):
    """
    Создает модель с формой для служебной записки
    """
    try:
        memo = Memo.query.filter_by(id=id).first()
        if not memo:
            return jsonify({"STATUS": "Error", "message": f"Memo with ID {id} not found"}), 404

        creator = Employees.query.filter_by(id=memo.id_of_creator).first()
        creator_user = Users.query.filter_by(id=memo.id_of_creator).first()
        executor = Employees.query.filter_by(id=memo.id_of_executor).first() if memo.id_of_executor else None

        descriptions = Description.query.filter_by(memo_id=id).all()
        description_list = []
        for desc in descriptions:
            executor_desc = Employees.query.filter_by(id=desc.id_of_executor).first() if desc.id_of_executor else None
            exec_user = Users.query.filter_by(id=desc.id_of_executor).first() if desc.id_of_executor else None
            department = Department.query.filter_by(id=executor_desc.department_id).first() if executor_desc else None
            unit = Units.query.filter_by(id=desc.unit_id).first() if desc.unit_id else None
            status = StatusOfPurchase.query.filter_by(id=desc.status_id).first() if desc.status_id else None

            description_list.append({
                "ID": desc.id,
                "POSITION": desc.pos,
                "NAME": desc.name,
                "COUNT": desc.count,
                "UNIT_CODE": desc.unit_id if unit else 0,
                "UNIT_TEXT": unit.short_name if unit else "",
                "STATUS_CODE": status.id if status else 0,
                "STATUS_TEXT": status.name if status else "",
                "COEF": status.coef if status else 0,
                "CONTRACT": desc.contract,
                "CONTRACT_INFO": desc.contract_info if desc.contract_info else "",
                "DATE_OF_DELIVERY": desc.date_of_delivery.strftime("%Y-%m-%d") if desc.date_of_delivery else "",
                "EXECUTOR": {
                    "ID": executor_desc.id if executor_desc else 0,
                    "SURNAME": executor_desc.surname if executor_desc else "",
                    "NAME": executor_desc.name if executor_desc else "",
                    "PATRONYMIC": executor_desc.patronymic if executor_desc else "",
                    "DEPARTMENT": department.name if department else "",
                    "PHONE": exec_user.phone if exec_user else "",
                    "EMAIL": exec_user.email if exec_user else ""
                }
            })
        
        status_memo = StatusOfExecution.query.filter_by(id = memo.status_id).first()
        department_creator = Department.query.filter_by(id=creator.department_id).first() if creator else None
        department_executor = Department.query.filter_by(id=executor.department_id).first() if executor else None
        data = {
            "ID_MEMO": memo.id,
            "DATE_OF_CREATION": memo.date_of_creation.strftime("%Y-%m-%d"),
            "DATE_OF_APPOINTMENT": memo.date_of_appointment.strftime("%Y-%m-%d") if memo.date_of_appointment else "",
            "STATUS_CODE": memo.status_id if status_memo else 0,
            "STATUS_TEXT": status_memo.name if status_memo else "",
            "INFO": memo.info,
            "JUSTIFICATION": memo.description if memo.description else "",
            "CREATOR": {
                "ID": creator.id,
                "SURNAME": creator.surname,
                "NAME": creator.name,
                "PATRONYMIC": creator.patronymic,
                "DEPARTMENT": department_creator.name if department_creator else "",
                "PHONE": creator_user.phone if creator_user else "",
                "EMAIL": creator_user.email if creator_user else ""
            },
            "EXECUTOR": {
                "ID": executor.id if executor else 0,
                "SURNAME": executor.surname if executor else "",
                "NAME": executor.name if executor else "",
                "PATRONYMIC": executor.patronymic if executor else "",
                "DEPARTMENT": department_executor.name if department_executor else ""
            },
            "DESCRIPTION": description_list
        }
        json_response = json.dumps(data, ensure_ascii=False, indent=4)
        return Response(json_response, content_type='application/json; charset=utf-8')
    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

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
                id = int(id)
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
                "ID": memo.id,
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
    try:
        # Получение данных пользователя из токена
        claims = get_jwt()  # Получаем дополнительные данные из токена
        role_id = claims.get("role_id")

        if role_id == 1:
            id_memo = request.args.get("id")
            status = request.args.get("accept")

            memo = Memo.query.filter_by(id = id_memo).first()
            memo.status_id = 2 if status else 3 # 2 - Зарегистрировна, 3 - Отклонена нач. отдела
            add_commit(memo)
        elif role_id == 2:
            id_memo = request.args.get("id")
            status = request.args.get("accept")

            memo = Memo.query.filter_by(id = id_memo).first()
            memo.status_id = 4 if status else 6 # 4 - Исполнение, 6 - Отклонена отделом закупок
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
        print(ex)
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
        expires = timedelta(hours=2) 
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

@app.route('/get_selectors', methods=['GET'])
def get_selectors():
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
    
@app.route('/test', methods=['GET'])
def test():
    a = "5"
    b = "05"
    c = "0005"
    return 0
    
#===================================================================================#
#--------------------------------РАБОТА С СОДЕРЖАНИЕМ-------------------------------#
#===================================================================================#

@app.route('/set_sop', methods=['POST'])
def set_sop():
    try:
        id = request.args.get("id")
        if id:
            desc = Description.query.filter_by(id = id).first()
            print(desc)
            desc.status_id += 1
            add_commit(desc)
            return jsonify({"STATUS": "Ok", "message": f"{id} status of purchase changed successfully"}), 200
        else:
            return jsonify({"STATUS": "Error", "message": "The \'id\' argument is not set"}), 400
    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500
    
@app.route('/get_aggregate', methods=['GET'])
@jwt_required()
def aggregate_description_data():
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



@app.route('/count_executor', methods=['GET'])
def count_all_executors():
    # Подсчёт уникальных memo_id в таблице Memo
    memo_counts = db.session.query(
        Memo.id_of_executor,
        func.count(func.distinct(Memo.id)).label('memo_count')
    ).filter(Memo.id_of_executor != None).group_by(Memo.id_of_executor).subquery()

    # Подсчёт уникальных memo_id в таблице Description
    description_counts = db.session.query(
        Description.id_of_executor,
        func.count(func.distinct(Description.memo_id)).label('description_count')
    ).filter(Description.id_of_executor != None).group_by(Description.id_of_executor).subquery()

    # Объединение подсчётов с информацией о сотрудниках
    combined_counts = db.session.query(
        Employees.id.label("executor_id"),
        Employees.name.label("name"),
        Employees.surname.label("surname"),
        Employees.patronymic.label("patronymic"),
        (func.coalesce(memo_counts.c.memo_count, 0) + 
         func.coalesce(description_counts.c.description_count, 0)).label("total_count")
    ).outerjoin(memo_counts, Employees.id == memo_counts.c.id_of_executor) \
     .outerjoin(description_counts, Employees.id == description_counts.c.id_of_executor) \
     .all()

    # Формирование результата
    result = {
        str(row["executor_id"]): {
            "NAME": row["name"],
            "SURNAME": row["surname"],
            "PATRONYMIC": row["patronymic"],
            "COUNT": row["total_count"]
        } for row in combined_counts
    }

    return jsonify(result), 200
