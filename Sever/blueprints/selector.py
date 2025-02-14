from flask import Blueprint
from Sever.selector import get_all_selectors

selector_bp = Blueprint('selector', __name__, url_prefix='/selector')

@selector_bp.route('/get_all', methods=['GET'])
def get_all():
    """
    Вызов функции Sever.selector.get_all_selectors() для получения всех редкоизменяемых вспомогательных списков из бд.
    """
    return get_all_selectors()