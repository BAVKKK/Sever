"""Вспомогательные ф-ции для бд"""
from flask import current_app, jsonify
from datetime import datetime as dt

from Sever import app, db, log_request
from Sever.models import *

def add_commit(param):
    """
    Сокращение для SQLAlchemy
    """
    db.session.add(param)
    db.session.commit()    

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

def add_description(memo_id, data):
    try:
        # Пока не удаляем из-за дат статусов
        # Удаляем все существующие записи к конкретной заявке

        # Description.query.filter_by(memo_id=memo_id).delete()
        # db.session.commit()

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
            
            if disc.get("ID") is None or disc.get("ID") == 0:
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

                new_his = HistoryOfchangingSOP(
                        date_of_setup = datetime.now().date(),
                        description_id = new_disc.id,
                        setted_status_id = new_disc.status_id
                )
                db.session.add(new_his)
            else:
                disk = Description.query.filter_by(id = disc.get("ID")).first()
                # Логика для обновления полей

                his = HistoryOfchangingSOP.query.filter_by(description_id = disc.get("ID")).first()
                # Логика для обновления полей
        
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