from flask import current_app, jsonify, Response
from sqlalchemy.orm import joinedload
import json

from Sever import db
from Sever.utils import log_request, add_commit
from Sever.models import Kanban, KanbanColumn

@log_request
def get_kanban(user_id):
    try:
        kanbans = (
            Kanban.query
            .join(KanbanColumn, Kanban.column_id == KanbanColumn.id)
            .filter(Kanban.user_id == user_id)
            .options(joinedload(Kanban.kanban_column))  # Загружаем связанные данные
            .all()
        )
        
        response = [{
            "ID": kanban.id,
            "COLUMN": kanban.kanban_column.name,
            "COLUMNID": kanban.column_id,
            "CONTENT": kanban.info
        } for kanban in kanbans]

        json_response = json.dumps(response, ensure_ascii=False, indent=4)
        return Response(json_response, content_type='application/json; charset=utf-8')

    except ValueError as ex:
        current_app.logger.error(f"Error in get_kanban: {ex}")
        raise ValueError(f"Error in get_kanban: {ex}")
    except Exception as ex:
        current_app.logger.error(f"Error in get_kanban: {ex}")
        raise RuntimeError(f"Error in get_kanban: {ex}")

@log_request
def set_kanban(user_id, json_data):
    try:
        for kanban in json_data:
            if not kanban.get("COLUMNID") or not kanban.get("CONTENT"):
                raise ValueError("Missing required kanban data (COLUMNID or CONTENT)")

        # Удаляем старые канбаны пользователя
        Kanban.query.filter_by(user_id=user_id).delete()
        db.session.commit()

        # Сохраняем новые канбаны
        for item in json_data:
            new_kanban = Kanban(
                user_id=user_id,
                column_id=item["COLUMNID"],
                info=item["CONTENT"]
            )
            add_commit(new_kanban)
        
        return jsonify({"STATUS": "Ok"}), 200

    except ValueError as ex:
        current_app.logger.error(f"Error in set_kanban: {ex}")
        raise ValueError(f"Error in set_kanban: {ex}")
    except Exception as ex:
        current_app.logger.error(f"Error in set_kanban: {ex}")
        raise RuntimeError(f"Error in set_kanban: {ex}")