from flask import Blueprint
from Sever.blueprints.auth import auth_bp
from Sever.blueprints.memo import memo_bp
from Sever.blueprints.reestr import reestr_bp
from Sever.blueprints.user import user_bp
from Sever.blueprints.selector import selector_bp
from Sever.blueprints.checklist import checklist_bp
from Sever.blueprints.kanban import kanban_bp
from Sever.blueprints.description import desc_bp

def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp) 
    app.register_blueprint(memo_bp)
    app.register_blueprint(selector_bp)
    app.register_blueprint(checklist_bp)
    app.register_blueprint(reestr_bp)
    app.register_blueprint(kanban_bp)
    app.register_blueprint(desc_bp)
