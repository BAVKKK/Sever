"""
Файл с функциями для /user
"""
from flask import current_app, Response
from sqlalchemy import func
import json

from Sever.utils import log_request
from Sever.extensions import db
from Sever.models import Employees, Roles, Department, Users

@log_request
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
        current_app.logger.error(f"Error in apply_users_filters: {ex}")
        raise ValueError(f"Error in apply_users_filters: {ex}")


@log_request
def get_users_info(filters):
    try:
        query = (
            db.session.query(
                Employees.id,
                Employees.surname,
                Employees.name,
                Employees.patronymic,
                Employees.post,
                Employees.department_id,
                Department.name.label("department_name"),
                Users.phone,
                Users.email
            )
            .join(Department, Employees.department_id == Department.id)
            .outerjoin(Users, Employees.id == Users.id)
        )

        if filters:
            if isinstance(filters, str):
                filters = json.loads(filters)
            query = apply_users_filters(query, filters)

        employees = query.order_by(Employees.department_id).all()
        
        # Формируем ответ
        response = {}
        for emp in employees:
            dep_id = emp.department_id
            if dep_id not in response:
                response[dep_id] = {"NAME": emp.department_name, "EMPLOYEES": []}
            
            response[dep_id]["EMPLOYEES"].append({
                "ID": emp.id,
                "SURNAME": emp.surname,
                "NAME": emp.name,
                "PATRONYMIC": emp.patronymic,
                "POST": emp.post,
                "PHONE": emp.phone or "",
                "EMAIL": emp.email or ""
            })

        json_response = json.dumps(response, ensure_ascii=False, indent=4)
        return Response(json_response, content_type='application/json; charset=utf-8')
    
    except ValueError as ex:
        current_app.logger.error(f"Error in get_users_info: {ex}")
        raise ValueError(f"Error in get_users_info: {ex}")
    except Exception as ex:
        current_app.logger.error(f"Error in get_users_info: {ex}")
        raise RuntimeError(f"Error in get_users_info: {ex}")


@log_request
def get_user_info(role_id, user_id):
    try:
        user = (
            db.session.query(
                Employees.id,
                Employees.surname,
                Employees.name,
                Employees.patronymic,
                Employees.post,
                Employees.department_id,
                Department.name.label("department_name"),
                Roles.id.label("role_id"),
                Roles.name.label("role_name"),
                Roles.comment.label("role_comment")
            )
            .outerjoin(Department, Employees.department_id == Department.id)
            .outerjoin(Roles, Roles.id == role_id)
            .filter(Employees.id == user_id)
            .first()
        )

        if not user:
            raise ValueError("User not found")
        
        data = {
            "ID": user.id,
            "SURNAME": user.surname,
            "NAME": user.name,
            "PATRONYMIC": user.patronymic,
            "POST": user.post,
            "ROLE": {
                "ID": user.role_id,
                "NAME": user.role_name,
                "COMMENT": user.role_comment
            },
            "DEPARTMENT": {
                "ID": user.department_id,
                "NAME": user.department_name if user.department_name else None
            }
        }

        json_response = json.dumps(data, ensure_ascii=False, indent=4)
        return Response(json_response, content_type='application/json; charset=utf-8')

    except Exception as ex:
        current_app.logger.error(f"Error in get_user_info: {ex}")
        raise RuntimeError(f"Error in get_user_info: {ex}")
