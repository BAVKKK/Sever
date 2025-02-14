from flask import current_app, request, jsonify, Response
from sqlalchemy import func
from sqlalchemy.orm import session
from datetime import datetime as dt

import json

from Sever.utils import log_request, add_commit
from Sever.db_utils import fill_zeros
from Sever.constants import *
from Sever.models import *

def set_contract_type(contract_type, ids):
    if not ids:
        raise ValueError("Invalid input: ids are missing or empty.")

    try:
        # Обновляем записи в таблице description
        db.session.query(Description).filter(Description.id.in_(ids)).update(
            {"contract_type": contract_type}, synchronize_session=False
        )
        db.session.commit()  # Фиксируем изменения

        return jsonify({"STATUS": "Success"}), 200

    except Exception as ex:
        db.session.rollback()  # Откатываем транзакцию в случае ошибки
        raise RuntimeError(f"Error during contract type update: {ex}")


def next_sop(current_sop, type):
    try:
        if type is None:
            return ConstantSOP.REQUEST_TKP

        if current_sop == ConstantSOP.NOT_SETTED:
            next_value = ConstantSOP.CONTRACT_RULES[type][0]         
        elif ConstantSOP.CONTRACT_RULES[type].index(current_sop) + 1 < len(ConstantSOP.CONTRACT_RULES[type]):
            next_value = ConstantSOP.CONTRACT_RULES[type][ConstantSOP.CONTRACT_RULES[type].index(current_sop) + 1]
        else:
            raise ValueError("Status not setted. Last value yet.")
        return next_value
    except Exception as ex:
        raise ValueError(f"{ex}")


def prev_sop(current_sop, type):
    try:
        if type is None or current_sop == ConstantSOP.NOT_SETTED:
            return ConstantSOP.NOT_SETTED
  
        if ConstantSOP.CONTRACT_RULES[type].index(current_sop) - 1 > 0:
            prev_value = ConstantSOP.CONTRACT_RULES[type][ConstantSOP.CONTRACT_RULES[type].index(current_sop) - 1]
            return prev_value
        else:
            return ConstantSOP.NOT_SETTED
   
    except Exception as ex:
        raise ValueError(f"{ex}")


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


def drop_sop(descs):
    """
    Функция изменяет текущий статус закупки на предыдущий и удаляет запись из истории изменений статуса.
    """
    try:
        # Получаем массив статусов из объектов descs
        status_ids = [desc.status_id for desc in descs]

        # Проверяем, что все элементы имеют один и тот же статус
        unique_statuses = set(status_ids)
        if len(unique_statuses) > 1:
            raise ValueError("All objects must have one status_id")
        
        # Получаем массив ID из объектов descs
        desc_ids = [desc.id for desc in descs]

        # Удаляем записи из истории изменений статусов
        HistoryOfchangingSOP.query.filter(
            HistoryOfchangingSOP.description_id.in_(desc_ids),
            HistoryOfchangingSOP.setted_status_id.in_(status_ids)
        ).delete()
        db.session.commit()

        # Получаем предыдущий статус (по первому объекту, т.к. все статусы одинаковые)
        prev_status = prev_sop(descs[0].status_id, descs[0].contract_type)
        ct = descs[0].contract_type

        if prev_status == ConstantSOP.NOT_SETTED:
            ct = None

        # Обновляем статусы у всех переданных объектов
        Description.query.filter(Description.id.in_(desc_ids)).update(
            {Description.status_id: prev_status, Description.contract_type: ct},
            synchronize_session=False
        )
        db.session.commit()

    except Exception as ex:
        raise RuntimeError(f"Unexpected error in drop_sop: {ex}")


def set_sop(ids):
    try:
        # Проверка на пустое значение id
        if not ids:
            raise ValueError("The 'ids' arguments are not set")     
        # Проверка, что ids - это список или другой итерируемый объект
        if not isinstance(ids, (list, tuple)):
            raise TypeError("The 'ids' argument must be a list or tuple of integers")
        # Проверка на то, что каждый элемент в ids является целым числом
        for id in ids:
            if not isinstance(id, int):
                raise ValueError(f"ID {id} must be an integer")
            # Получение записи из базы данных
            desc = Description.query.filter_by(id=id).first()
            if not desc:
                raise ValueError(f"Description with id {id} not found")
            # Обновление статуса
            desc.status_id = next_sop(desc.status_id, desc.contract_type)
            add_commit(desc)
            # Обновление истории
            his = HistoryOfchangingSOP.query.filter_by(description_id=id).first()
            create_his(desc.id, desc.status_id)
        # Если всё прошло успешно
        return jsonify({"STATUS": "Ok", "message": "Status of purchase changed successfully"}), 200
    except ValueError as ve:
        # Если ошибка из-за некорректных данных (ValueError)
        raise ValueError(f"Error in set_sop: {ve}")     
    except TypeError as te:
        # Если ошибка из-за неправильного типа данных (TypeError)
        raise TypeError(f"Error in set_sop: {te}")
    except Exception as ex:
        # Все другие ошибки
        raise RuntimeError(f"Unexpected error in set_sop: {ex}")


def valid_ag_params(role_id, user_id):
    """
    Проверяем значения из токена
    """
    try:
        if not role_id:
            raise ValueError("Role_id is missing")
        elif Roles.query.filter_by(id=role_id).first() is None:
            raise PermissionError(f"Role with setted id {role_id} not found")
        elif role_id not in [ConstantRolesID.MTO_CHEF_ID, ConstantRolesID.MTO_EMPLOYEE_ID]:
            raise PermissionError("Unauthorized role")

        if not user_id:
            raise ValueError("User_id is missing")
        elif Users.query.filter_by(id=user_id).first() is None:
            raise ValueError(f"User with setted id {user_id} not found")

    except ValueError as ex:
        raise ValueError(f"{ex}")
    except PermissionError as ex:
        raise PermissionError(f"{ex}")
    except Exception as ex:
        raise RuntimeError(f"{ex}")


def create_aggregate_query(role_id, user_id, status=None):
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

    if status is not None:
        query_aggregated = query_aggregated.filter(Description.status_id == status)
    
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
    
    return query_aggregated


def create_details_query(status=None):
    query_details = db.session.query(
            Description.id,
            Description.memo_id,
            Description.name,
            Description.count
        )
    if status is not None:
        query_details = query_details.filter(Description.status_id == status)

    return query_details


def create_details_dict(details_data):
    try:
        details_by_memo = {}
        for row in details_data:
            key = (row.memo_id, row.name)
            if key not in details_by_memo:
                details_by_memo[key] = []
            details_by_memo[key].append({
                "ID": row.id,
                "MEMO_ID": fill_zeros(row.memo_id),
                "COUNT": row.count
            })
        return details_by_memo
    except Exception as ex:
        raise RuntimeError(f"{ex}")


def create_ag_result(details_by_memo, aggregated_data):
    """
    Формируем результат агреггированных позиций
    """
    try:
        result = {}
        for row in aggregated_data:
            key = (row.name, row.short_name)  # Комбинированный ключ: по наименованию и единице измерения
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
        return result
    except Exception as ex:
        raise RuntimeError(f"{ex}")


def aggregate_data(role_id, user_id, status):
    """
    Агрегация данных по memo_id и name с учетом ролей и статуса memo.
    """
    try:
        # Проверяем параметры полученные из токена
        valid_ag_params(role_id, user_id)

        # Первый запрос: агрегированные данные
        query_aggregated = None

        # Второй запрос: детали (без группировки)
        query_details = None

        if status is not None:
            count = db.session.query(func.count(StatusOfPurchase.id)).scalar()
            if int(status) > 0 and int(status) <= count:
                query_aggregated = create_aggregate_query(role_id=role_id, user_id=user_id, status=status)
                query_details = create_details_query(status)          
            else:
                raise ValueError("Unknown status")
        else:
            query_aggregated = create_aggregate_query(role_id=role_id, user_id=user_id)
            query_details = create_details_query()    

        aggregated_data = query_aggregated.all()

        details_data = query_details.all()

        # Создаем словарь для быстрого доступа к деталям
        details_by_memo = create_details_dict(details_data)

        # Формируем итоговую структуру
        result = create_ag_result(details_by_memo=details_by_memo, aggregated_data=aggregated_data)
        
        # Теперь объединяем все записи в список
        final_result = list(result.values())
        json_response = json.dumps(final_result, ensure_ascii=False, indent=4)
        return Response(json_response, content_type='application/json; charset=utf-8')

    except PermissionError as ex:
        raise PermissionError(f"{ex}")

    except ValueError as ex:
        raise ValueError(f"{ex}")

    except Exception as ex:
        raise RuntimeError(f"Unexpected error in aggregate_data: {ex}")

