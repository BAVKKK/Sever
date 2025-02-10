from flask import render_template, redirect, url_for, request, flash, session, jsonify, Response
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_jwt_extended import get_jwt
from sqlalchemy import text, func, or_
from sqlalchemy.orm import joinedload
from collections import namedtuple, defaultdict
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

# Добавить удаление мемо при ошибке в дескрипшен

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
        # Определяем базовый запрос
        query = Memo.query

        # Определяем фильтрацию по ролям
        if role_id == ConstantRolesID.DEPARTMENT_CHEF_ID:
            # Для роли "Руководитель отдела"
            department_id = user.department_id  # Получаем department_id руководителя
            query = query.filter(Memo.id_of_creator.in_(
                db.session.query(Employees.id).filter_by(department_id=department_id)
            ))
        elif role_id in [ConstantRolesID.MTO_CHEF_ID, ConstantRolesID.COMPANY_LEAD_ID]: # Пока на эти роли нет никакой особой логике, но если убрать поймаем 403
            pass
        elif role_id == ConstantRolesID.EMPLOYEE_ID:  # Если пользователь сотрудник
            # Получаем заявки, где user.id либо в id_executor, либо в id_creator
            query = query.filter(
                (Memo.id_of_executor == user_id) | (Memo.id_of_creator == user_id)
            )
        elif role_id == ConstantRolesID.MTO_EMPLOYEE_ID:  # Если пользователь сотрудник отдела МТО
            # Получаем только те заявки, где пользователь указан в id_executor
            query = query.filter(Memo.id_of_executor == user_id)
        else:
            return jsonify({"msg": "Unauthorized role"}), 403

        statuses = SOEForRoles[role_id]
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

def next_sop(current_sop, type):
    try:
        if type is None:
            type = ConstantSOP.CONTRACT_TYPE["Contract"] # По умолчанию установим тип договора как обычный договор
        if current_sop == ConstantSOP.NOT_SETTED:
            next_value = ConstantSOP.CONTRACT_RULES[type][0]         
        elif ConstantSOP.CONTRACT_RULES[type].index(current_sop) + 1 < len(ConstantSOP.CONTRACT_RULES[type]):
            next_value = ConstantSOP.CONTRACT_RULES[type][ConstantSOP.CONTRACT_RULES[type].index(current_sop) + 1]
        else:
            raise ValueError("Status not setted. Last value yet.")
        return next_value
    except Exception as ex:
        raise ValueError(f"{ex}")

@app.route('/set_sop', methods=['POST'])
def set_sop():
    try:
        id = request.args.get("id")
        if id:
            desc = Description.query.filter_by(id = id).first()
            desc.status_id = next_sop(desc.status_id, desc.contract_type)
            add_commit(desc)
            his = HistoryOfchangingSOP.query.filter_by(description_id = id).first()
            create_his(desc.id , desc.status_id)
            return jsonify({"STATUS": "Ok", "message": f"{id} status of purchase changed successfully"}), 200
        else:
            return jsonify({"STATUS": "Error", "message": "The \'id\' argument is not set"}), 400
    except ValueError as ve:
        return jsonify({"STATUS": "Error", "message": str(ve)}), 400
    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500


@app.route('/get_aggregate', methods=['GET'])
@jwt_required()
def aggregate_description_data():
    """
    Агрегация данных по memo_id и name с учетом ролей и статуса memo.
    """
    try:
        claims = get_jwt()
        role_id = claims.get("role_id")
        user_id = claims.get("id")

        status = request.args.get("status")

        # Первый запрос: агрегированные данные
        query_aggregated = db.session.query(
            Description.memo_id,
            Description.name,
            Description.contract_type,
            func.sum(Description.count).label('total_count'),
            Units.short_name.label('short_name'),
            Units.full_name.label('full_name'),
            Memo.status_id
        ).join(Units, Description.unit_id == Units.id)
        query_aggregated = query_aggregated.join(Memo, Description.memo_id == Memo.id)

        # Второй запрос: детали (без группировки)
        query_details = db.session.query(
            Description.id,
            Description.memo_id,
            Description.name,
            Description.count
        )

        if status is not None:
            count = db.session.query(func.count(StatusOfPurchase.id)).scalar()
            if int(status) > 0 and int(status) <= count:
                query_aggregated = query_aggregated.filter(Description.status_id == status)
                query_details = query_details.filter(Description.status_id == status)
            else:
                return jsonify({"STATUS": "Error", "message": "Unknown status"}), 400
        

        query_aggregated = query_aggregated.group_by(
            Description.memo_id,
            Description.name,
            Description.contract_type,
            Units.short_name,
            Units.full_name,
            Memo.status_id
        )

        # Фильтрация по ролям
        if role_id == ConstantRolesID.MTO_CHEF_ID:
            allowed_statuses = SOEForRoles.get(ConstantRolesID.MTO_CHEF_ID, [])
            query_aggregated = query_aggregated.filter(Memo.status_id.in_(allowed_statuses))
        elif role_id == ConstantRolesID.MTO_EMPLOYEE_ID:
            query_aggregated = query_aggregated.filter(Description.id_of_executor == user_id) # Здесь статусы не проверяются, т.к. если исполнитель назначен, то статус уже должен быть не ниже уровня Зарегестрировано
        else:
            return jsonify({"STATUS": "Error", "message": "Unauthorized role"}), 403

        aggregated_data = query_aggregated.all()

        details_data = query_details.all()

        # Создаем словарь для быстрого доступа к деталям
        details_by_memo = {}
        for row in details_data:
            key = (row.memo_id, row.name)
            if key not in details_by_memo:
                details_by_memo[key] = []
            details_by_memo[key].append({
                "ID": row.id,
                "MEMO_ID": row.memo_id,
                "COUNT": row.count
            })

        # Формируем итоговую структуру
        result = {}
        for row in aggregated_data:
            key = (row.name, row.short_name)  # Теперь ключ будет комбинированным: по наименованию и единице измерения
            if key not in result:
                result[key] = {
                    "NAME": row.name,
                    "TOTAL_COUNT": 0,
                    "CONTRACT_TYPE": row.contract_type,
                    "SHORT_NAME": row.short_name,
                    "FULL_NAME": row.full_name,
                    "BY_MEMO": []
                }

            # Агрегируем количество
            result[key]["TOTAL_COUNT"] += row.total_count

            # Добавляем детали в BY_MEMO
            memo_details = details_by_memo.get((row.memo_id, row.name), [])
            for detail in memo_details:
                result[key]["BY_MEMO"].append(detail)

        # Теперь объединяем все записи в список
        final_result = list(result.values())
        json_response = json.dumps(final_result, ensure_ascii=False, indent=4)
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


@app.route('/set_contract_type', methods=['POST'])
def set_contract_type():
    try:
        contract_type = request.args.get("type")
        ids = request.get_json()  # Получаем список ID из тела запроса

        if not contract_type or not ids:
            return jsonify({"STATUS": "Error", "message": "Missing required parameters"}), 400

        # Обновляем записи в таблице description
        db.session.query(Description).filter(Description.id.in_(ids)).update(
            {"contract_type": contract_type}, synchronize_session=False
        )

        db.session.commit()  # Фиксируем изменения

        return jsonify({"STATUS": "Success"}), 200

    except Exception as ex:
        db.session.rollback()  # Откатываем транзакцию в случае ошибки
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500


@app.route('/create_checklist', methods=['POST'])
def create_checklist():
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

        # Проверка наличия VALUES
        values = json_data.get("VALUES", [])
        if not values:
            return jsonify({"STATUS": "Error", "message": "VALUES list is empty"}), 400

        # Оптимизированная проверка Description
        desc_ids = [i["ID"] for i in values]
        existing_descs = {desc.id for desc in Description.query.filter(Description.id.in_(desc_ids)).all()}

        for i in values:
            if i["ID"] not in existing_descs:
                raise DescError(f"""Description with ID {i["ID"]} does not exist""")
            cld = ChecklistData.query.filter_by(description_id = i["ID"]).first()
            if cld is not None and cld.checklist_id != cl_id:
                raise DescError(f"""Description with ID {i["ID"]} is already in ChecklistData""")
            elif cld is not None and cld.checklist_id == cl_id:
                pass
            else:
                new_checklist_data = ChecklistData(
                    checklist_id=cl_id,
                    description_id=i["ID"]
                )
                db.session.add(new_checklist_data)
        db.session.commit()
        return jsonify({"STATUS": "Success"}), 200

    except DescError as ex:
        # Удаление чеклиста и связанных данных при ошибке
        ChecklistData.query.filter_by(checklist_id=cl_id).delete()
        Checklist.query.filter_by(id=cl_id).delete()
        db.session.commit()
        return jsonify({"STATUS": "Error", "message": str(ex)}), 400

    except Exception as ex:
        db.session.rollback()  # Откатываем транзакцию в случае ошибки
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500


@app.route('/get_checklist', methods=['GET'])
@jwt_required()
def get_checklist():
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
            Units.short_name,
            Units.full_name
        ).join(Checklist, Checklist.id == ChecklistData.checklist_id
        ).join(Description, Description.id == ChecklistData.description_id
        ).join(Units, Units.id == Description.unit_id
        ).filter(Description.id_of_executor == user_id).all()

        # Группируем данные по CHECKLIST_ID
        checklist_data = {}
        for checklist_id, description_id, description_name, memo_id, count, unit_short_name, unit_full_name in query_result:
            if checklist_id not in checklist_data:
                checklist_data[checklist_id] = []
            
            checklist_data[checklist_id].append({
                "ID": description_id,
                "NAME": description_name,
                "MEMO_ID": memo_id,
                "COUNT": count,
                "UNIT_SHORT_NAME": unit_short_name,
                "UNIT_FULL_NAME": unit_full_name,
            })

        # Формируем список всех чек-листов
        response = [
            {"CHECKLIST_ID": cl_id, "VALUES": values}
            for cl_id, values in checklist_data.items()
        ]

        json_response = json.dumps(response, ensure_ascii=False, indent=4)
        return Response(json_response, content_type='application/json; charset=utf-8')

    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500



