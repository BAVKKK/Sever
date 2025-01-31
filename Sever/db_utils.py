"""Вспомогательные ф-ции для бд"""
from flask import current_app, jsonify
from datetime import datetime as dt

from Sever import app, db, log_request
from Sever.models import *
from Sever.db.utils import save_file
from sqlalchemy import func


def fill_zeros(number):
    if not (0 <= number <= 9999):
        raise ValueError("Число должно быть в диапазоне от 0 до 9999")
    return f"{number:04d}"

def remove_leading_zeros(s):
    if not s.isdigit():
        raise ValueError("Строка должна содержать только цифры")
    return int(s)  # int автоматически убирает ведущие нули

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

@log_request
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
            print(disc.get("ID"))
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
                db.session.add(old_disc)

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
        # Пока не работает, т.к. всегда ответственный начальник 13 отдела, а именно 7
        #memo.id_of_executor = data["EXECUTOR"]["ID"] if data["EXECUTOR"]["ID"] is not None and data["EXECUTOR"]["ID"] != 0 else None
        memo.id_of_executor = Users.query.filter_by(role_id = 2).first().id # Подставляем актуальное ID руководителя 13 отдела
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
        for row in combined_counts:
            if row["total_count"] != 0 and row["executor_id"] != 7:
                response[str(row["executor_id"])] ={
                        "SURNAME": row["surname"],
                        "NAME": row["name"],
                        "PATRONYMIC": row["patronymic"],
                        "COUNT": row["total_count"]
                    }

        return response
    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500