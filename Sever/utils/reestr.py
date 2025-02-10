from flask import current_app, request, jsonify, Response
from sqlalchemy import or_
from sqlalchemy.orm import joinedload, aliased
from collections import namedtuple, defaultdict

import json

from Sever.models import *
from Sever.db_utils import fill_zeros
from Sever.constants import ConstantRolesID, SOEForRoles


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
            # Создаем алиас для таблицы Description на случай, если её уже джоинили
            desc_as = aliased(Description)
            query = query.join(desc_as).filter(desc_as.name.ilike(f"%{filt}%"))
        if 'EXECUTOR_NAME' in filters:
            filt = filters["EXECUTOR_NAME"]
            # Создаем алиас для второй таблицы Description
            desc_alias = aliased(Description)
            query = query.join(desc_alias, desc_alias.memo_id == Memo.id) \
                         .join(Employees, Employees.id == desc_alias.id_of_executor) \
                         .filter(
                             or_(
                                 Employees.name.ilike(f"%{filt}%"),
                                 Employees.surname.ilike(f"%{filt}%"),
                                 Employees.patronymic.ilike(f"%{filt}%")
                             )
                         )
        return query
    except Exception as ex:
        raise RuntimeError(f"{ex}")

def valid_gr_params(user_id, role_id):
    """
    Проверяем значения из токена
    """
    try:
        if not role_id:
            raise ValueError("Role_id is missing")
        elif Roles.query.filter_by(id=role_id).first() is None:
            raise PermissionError(f"Role with setted id {role_id} not found")

        if not user_id:
            raise ValueError("User_id is missing")
        elif Users.query.filter_by(id=user_id).first() is None:
            raise ValueError(f"User with setted id {user_id} not found")
        elif Employees.query.filter_by(id=user_id).first() is None:
            raise ValueError(f"User_id and Employee_id doesn't matched. Employee with setted user_id not found!!!")

    except ValueError as ex:
        raise ValueError(f"{ex}")
    except PermissionError as ex:
        raise PermissionError(f"{ex}")
    except Exception as ex:
        raise RuntimeError(f"{ex}")


def apply_roles(query, role_id, user_id):
    try:
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
            # Получаем заявки, где user.id в id_creator
            query = query.filter(
                (Memo.id_of_creator == user_id)
            )
        elif role_id == ConstantRolesID.MTO_EMPLOYEE_ID:  # Если пользователь сотрудник отдела МТО
            # Получаем только те заявки, где пользователь указан в id_executor
            query = query.join(Description, Description.memo_id == Memo.id).filter(Description.id_of_executor == user_id)
        else:
            return jsonify({"msg": "Unauthorized role"}), 403
        
        return query
    except Exception as ex:
        raise RuntimeError(f"{ex}")


def apply_status(query, role_id, status=None):
    try:
        statuses = SOEForRoles[role_id]
        # Применяем фильтр по статусу, если передан
        if status is not None:
            if int(status) in statuses:
                query = query.filter(Memo.status_id == status)
            else:
                msg = f"Incorrect status_id ({status}) for this role. Current role_id is {role_id}. Available statuses is {statuses}"
                raise ValueError(f"{msg}")
        else:
            query = query.filter(Memo.status_id.in_(statuses))

        return query
    except ValueError as ex:
        raise ValueError(f"{ex}")
    except Exception as ex:
        raise RuntimeError(f"{ex}")


def get_reestr(user_id, role_id, status=None, filters=None):
    """
    Получить реестр
    """
    try:
        valid_gr_params(user_id=user_id, role_id=role_id)

        user = Employees.query.filter_by(id=user_id).first()
        # Определяем базовый запрос
        query = Memo.query
        # Применяем фильтры по ролям
        query = apply_roles(query=query, role_id=role_id, user_id=user_id)
        # Применяем фильтры по статусам
        query = apply_status(query=query, role_id=role_id, status=status)

        # Применяем остальные фильтры, если они переданы
        if filters:
            query = apply_reestr_filters(query=query, filters=filters)

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

    except ValueError as ex:
        raise ValueError(f"{ex}")
    except PermissionError as ex:
        raise PermissionError(f"{ex}")
    except Exception as ex:
        raise RuntimeError(f"{ex}")

