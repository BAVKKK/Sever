"""Вспомогательные ф-ции для бд"""
from flask import current_app, jsonify, Response
from datetime import datetime as dt

import json

from Sever.utils import log_request, add_commit
from Sever.extensions import db
from Sever.models import *
from Sever.database.minio_lib import *
from Sever.database.utils import *
from sqlalchemy import func
from Sever.constants import *

class DescError(Exception):
    pass

def fill_zeros(number):
    if not isinstance(number, int):
        raise TypeError("Value must be an integer")
    if not (0 < number <= 9999):
        raise ValueError("Value must be in [1; 9999]")
    return f"{number:04d}"

def remove_leading_zeros(s):
    s = s.strip('"')  # Удаляем кавычки
    if not s:
        raise ValueError("String is empty")
    if not s.isdigit():
        raise ValueError("Only numbers can be used")
    return int(s)  # int автоматически убирает ведущие нули

def create_his(desc_id, sop_id):
    """
    Создаем новую запись в истории изменения статуса закупки
    """
    new_his = HistoryOfchangingSOP(
        date_of_setup = dt.now(),
        description_id = desc_id,
        setted_status_id = sop_id
        )
    add_commit(new_his)
    return new_his

@log_request
def add_description(memo_id, data):
    try:
        # Пока не удаляем из-за дат статусов
        # (Удаляем все существующие записи к конкретной заявке)

        # Description.query.filter_by(memo_id=memo_id).delete()
        # db.session.commit()

        # Добавляем новые записи
        for disc in data:
            date_of_delivery = None
            executor_id = None
            contract_type = None

            if disc.get("DATE_OF_DELIVERY"):
                try:
                    date_of_delivery = dt.strptime(disc["DATE_OF_DELIVERY"], "%Y-%m-%d").date()
                except ValueError:
                    raise ValueError(f"Invalid date format: {disc['DATE_OF_DELIVERY']}")
            if disc.get("EXECUTOR"):
                executor_id = disc["EXECUTOR"]["ID"]
            
            if disc.get("CONTRACT_TYPE") and disc.get("CONTRACT_TYPE") != "":
                contract_type = disc.get("CONTRACT_TYPE") if disc.get("CONTRACT_TYPE") not in ["", None] else None
                if disc.get("STATUS_CODE") and disc.get("STATUS_CODE") not in ConstantSOP.CONTRACT_RULES[contract_type]:
                    raise ValueError("Status code not in contract rules for this contract type!")

            if disc.get("ID") is None or disc.get("ID") == 0:
                new_disc = Description(
                    memo_id=memo_id,
                    pos=disc.get("POSITION"),
                    name=disc.get("NAME"),
                    count=disc.get("COUNT", 0),
                    unit_id=disc.get("UNIT_CODE"),
                    status_id=disc.get("STATUS_CODE"),
                    date_of_delivery=date_of_delivery,
                    id_of_executor = executor_id
                )
                add_commit(new_disc)

                new_his = HistoryOfchangingSOP(
                        date_of_setup = dt.now(),
                        description_id = new_disc.id,
                        setted_status_id = new_disc.status_id
                )
                add_commit(new_his)
            else:
                old_disc = Description.query.filter_by(id = disc.get("ID")).first()
                # Логика для обновления полей
                old_disc.pos = disc.get("POSITION")
                old_disc.name = disc.get("NAME")
                old_disc.count = disc.get("COUNT", 0)
                old_disc.unit_id = disc.get("UNIT_CODE")
                old_disc.status_id = disc.get("STATUS_CODE")
                old_disc.date_of_delivery = date_of_delivery
                old_disc.id_of_executor = executor_id
                old_disc.contract_type = contract_type
                db.session.add(old_disc)

                his = HistoryOfchangingSOP.query.filter_by(description_id = disc.get("ID")).first()
                # Логика для обновления полей
        
        db.session.commit()
        return jsonify({"STATUS": "Success", "message": "Descriptions added successfully"}), 200
    
    except Exception as ex:
        db.session.rollback()
        current_app.logger.error(ex)
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
            data["ID_MEMO"] = remove_leading_zeros(data["ID_MEMO"])
            memo = Memo.query.filter_by(id=data["ID_MEMO"]).first()

        # Добавление или обновление данных в служебках
        date_of_appointment = dt.strptime(data["DATE_OF_APPOINTMENT"], "%Y-%m-%d").date() if data["DATE_OF_APPOINTMENT"] else None
        memo.info = data["INFO"]
        # Пока не работает, т.к. всегда ответственный начальник 13 отдела, а именно 7
        #memo.id_of_executor = data["EXECUTOR"]["ID"] if data["EXECUTOR"]["ID"] is not None and data["EXECUTOR"]["ID"] != 0 else None
        memo.id_of_executor = Users.query.filter_by(role_id = ConstantRolesID.MTO_CHEF_ID).first().id # Подставляем актуальное ID руководителя 13 отдела
        memo.date_of_appointment = date_of_appointment

        memo.description = data["JUSTIFICATION"]
        memo.status_id = data["STATUS_CODE"] if data["STATUS_CODE"] and data["STATUS_CODE"] != 0 else 1
        if "HEAD_COMMENT" in data:
            memo.head_comment = data["HEAD_COMMENT"]
        if "EXECUTOR_COMMENT" in data:
            memo.executor_comment = data["EXECUTOR_COMMENT"]
        if "JUSTIFICATION_FILE" in data and data["JUSTIFICATION_FILE"] is not None:
            save_file(memo.id, data["JUSTIFICATION_FILE"], folder='justifications')
            memo.file_ext = data["JUSTIFICATION_FILE"]["EXT"]
            memo.filename = data["JUSTIFICATION_FILE"]["NAME"]

        add_commit(memo)
        err = add_description(memo.id, data["DESCRIPTION"])
        current_app.logger.info({"STATUS": "Success", "ID": memo.id})
        return jsonify({"STATUS": "Success", "ID": memo.id}), 200

    except Exception as ex:
        current_app.logger.error(ex)
        db.session.rollback()
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

def description_for_memo_form(descriptions):
    description_list = []
    for desc in descriptions:
        executor_desc = Employees.query.filter_by(id = desc.id_of_executor).first() if desc.id_of_executor else None
        exec_user = Users.query.filter_by(id = desc.id_of_executor).first() if desc.id_of_executor else None
        department = Department.query.filter_by(id = executor_desc.department_id).first() if executor_desc else None
        unit = Units.query.filter_by(id = desc.unit_id).first() if desc.unit_id else None
        status = StatusOfPurchase.query.filter_by(id = desc.status_id).first() if desc.status_id else None

        his = HistoryOfchangingSOP.query.filter_by(description_id = desc.id).all()
        history = []
        for hi in his:
            tmp = {
                "STATUS_ID": hi.setted_status_id,
                "DATE": hi.date_of_setup.strftime("%Y-%m-%d")
            }
            history.append(tmp)

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
            "DATE_OF_DELIVERY": desc.date_of_delivery.strftime("%Y-%m-%d") if desc.date_of_delivery else "",
            "CONTRACT_TYPE": desc.contract_type if desc.contract_type else "",
            "EXECUTOR": {
                "ID": executor_desc.id if executor_desc else 0,
                "SURNAME": executor_desc.surname if executor_desc else "",
                "NAME": executor_desc.name if executor_desc else "",
                "PATRONYMIC": executor_desc.patronymic if executor_desc else "",
                "DEPARTMENT": department.name if department else "",
                "PHONE": exec_user.phone if exec_user else "",
                "EMAIL": exec_user.email if exec_user else ""
            },
            "HISTORY": history
        })
    return description_list
        
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
        description_list = description_for_memo_form(descriptions)
        
        status_memo = StatusOfExecution.query.filter_by(id = memo.status_id).first()
        department_creator = Department.query.filter_by(id=creator.department_id).first() if creator else None
        department_executor = Department.query.filter_by(id=executor.department_id).first() if executor else None
        justification = {
            "EXT": None,
            "NAME": None,
            "DATA": None
        }
        if id is not None:
            mime_types = {
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
                'application/msword': '.doc',
                'application/pdf': '.pdf',
                'image/jpeg': '.jpeg',
                'image/png': '.png',
                'application/x-zip-compressed': '.zip'
            }
            if memo.filename is not None:
                objects = client.list_objects(bucket_name='sever', prefix=f'{id}/justifications/')
                justi_file = None
                for obj in objects: # Тут цикл потому что не знаю как иначе вытащить обж из "Минио обжекст"
                    if obj is not None:
                        justi_file = obj
                if justi_file is not None:
                    filename = memo.filename
                    minio_id = f"{id}/justifications/{filename}{mime_types[memo.file_ext]}"
                    data = f'data:{mime_types[memo.file_ext]};base64,{from_minio_to_b64str(minio_id, "sever")}'
                    justification["EXT"] = memo.file_ext
                    justification["DATA"] = data
                    justification["NAME"] = memo.filename
        data = {
            "ID_MEMO": fill_zeros(memo.id),
            "DATE_OF_CREATION": memo.date_of_creation.strftime("%Y-%m-%d"),
            "DATE_OF_APPOINTMENT": memo.date_of_appointment.strftime("%Y-%m-%d") if memo.date_of_appointment else "",
            "STATUS_CODE": memo.status_id if status_memo else 0,
            "STATUS_TEXT": status_memo.name if status_memo else "",
            "INFO": memo.info,
            "JUSTIFICATION": memo.description if memo.description else "",
            "HEAD_COMMENT": memo.head_comment if memo.head_comment else "",
            "EXECUTOR_COMMENT": memo.executor_comment if memo.executor_comment else "",
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
            "DESCRIPTION": description_list,
            "JUSTIFICATION_FILE": justification
        }
        json_response = json.dumps(data, ensure_ascii=False, indent=4)
        return Response(json_response, content_type='application/json; charset=utf-8')
    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

def count_memo_by_status():
    """
    Метод для подсчета заявок по статусам
    """
    try:
        statuses = StatusOfExecution.query.all()
        res = {}
        for status in statuses:
            # Используем filter для подсчета строк, соответствующих условию
            count = db.session.query(func.count()).filter(Memo.status_id == status.id).scalar()
            res[status.name] = count
        return res
    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

def count_memo_by_executor():
    """
    Подсчитывает количество уникальных memo_id для каждого исполнителя (id_of_executor)
    в таблицах Memo и Description, объединяет результаты и возвращает информацию о сотрудниках.
    """
    try:
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

        # Преобразуем результат в список словарей
        combined_counts = [row._asdict() for row in combined_counts]

        # Если данных нет, возвращаем сообщение
        if not combined_counts:
            return jsonify({"STATUS": "Success", "message": "No data found"}), 200

        # Формирование результата
        response = {} 
        current_mto_chef_id = Users.query.filter_by(role_id = ConstantRolesID.MTO_CHEF_ID).first().id
        for row in combined_counts:
            if row["total_count"] != 0 and row["executor_id"] != current_mto_chef_id:
                response[str(row["executor_id"])] ={
                        "SURNAME": row["surname"],
                        "NAME": row["name"],
                        "PATRONYMIC": row["patronymic"],
                        "COUNT": row["total_count"]
                    }
        return response
    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500

def db_create_checklist():
    try:
        new_cl = Checklist(
            date_of_creation = dt.now()
        )
        add_commit(new_cl)
        return new_cl.id
    except Exception as ex:
        raise CreateError(f"{ex}")

