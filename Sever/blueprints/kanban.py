from flask import current_app, Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt

from Sever.utils import log_request
from Sever.utils.kanban import set_kanban, get_kanban

kanban_bp = Blueprint('kanban', __name__, url_prefix='/kanban')

@kanban_bp.route('/', methods=['GET', 'POST'])
@jwt_required()
@log_request
def kanban():
    """
    Метод для записи канбана в БД (POST)
    или
    Метод для получения канбана из БД (GET)
    """
    try:
        # Получение данных пользователя из токена
        claims = get_jwt()  # Получаем дополнительные данные из токена
        user_id = claims.get("id")
        if not user_id:
            raise ValueError("User ID not found in token")
        if request.method == "POST":
            
            json_data = request.get_json()
            return set_kanban(user_id, json_data)
        
        if request.method == "GET":
            return get_kanban(user_id)

    except ValueError as ex:
        current_app.logger.error(f"ValueError in kanban: {ex}")
        return jsonify({"STATUS": "Error", "message": str(ex)}), 400
    except Exception as ex:
        current_app.logger.error(f"Unknown error in kanban: {ex}")
        return jsonify({"STATUS": "Error", "message": "Internal server error"}), 500
