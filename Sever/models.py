from Sever import db
from flask_login import UserMixin
import datetime


class Users(db.Model, UserMixin):
    __tablename__='users'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(128), nullable=False, unique=True)
    hash_pwd = db.Column(db.String(), nullable=False)
    email = db.Column(db.String(128), unique=True)
    phone = db.Column(db.String(32), unique=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=True)

class Roles(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    comment = db.Column(db.String, nullable=False)  

class StatusOfExecution(db.Model):
    __tablename__ = 'status_of_execution'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(36), nullable=True)

class StatusOfPurchase(db.Model):
    __tablename__ = 'status_of_purchase'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(36), nullable=True)
    coef = db.Column(db.Float, nullable=True)
    coef2 = db.Column(db.Float, nullable=True)

class Units(db.Model):
    __tablename__ = 'units'
    id = db.Column(db.Integer, primary_key=True)
    short_name = db.Column(db.String(64), nullable=True)
    full_name = db.Column(db.String(64), nullable=True)

class Department(db.Model):
    __tablename__ = 'department'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=True)

class Employees(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    surname = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    patronymic = db.Column(db.String(64), nullable=True)
    post = db.Column(db.String(64), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    
class Memo(db.Model):
    __tablename__ = 'memo'
    id = db.Column(db.Integer, primary_key=True)
    date_of_creation = db.Column(db.DateTime, nullable=True)
    info = db.Column(db.String, nullable=True)
    description = db.Column(db.String, nullable=True)
    id_of_creator = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    date_of_appointment = db.Column(db.DateTime, nullable=True)
    status_id = db.Column(db.Integer, db.ForeignKey('status_of_execution.id'), nullable=True)
    id_of_executor = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    head_comment = db.Column(db.String, nullable=True)
    executor_comment = db.Column(db.String, nullable=True)

    file_ext = db.Column(db.String(256), nullable=True)
    filename = db.Column(db.String(128), nullable=True)
    
class Description(db.Model):
    __tablename__ = 'description'
    id = db.Column(db.Integer, primary_key=True)
    memo_id = db.Column(db.Integer, db.ForeignKey('memo.id'), nullable=True)
    pos = db.Column(db.Integer, nullable=True)
    name = db.Column(db.String(128), nullable=True)
    count = db.Column(db.Integer, nullable=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    status_id = db.Column(db.Integer, db.ForeignKey('status_of_purchase.id'), nullable=True)
    date_of_delivery = db.Column(db.DateTime, nullable=True)
    id_of_executor = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    contract_type = db.Column(db.Integer, nullable=True)

class HistoryOfchangingSOP(db.Model):
    __tablename__ = 'history_of_changing_sop'
    id = db.Column(db.Integer, primary_key=True)
    date_of_setup = db.Column(db.DateTime, nullable=True)
    description_id = db.Column(db.Integer, db.ForeignKey('description.id'), nullable=True)
    setted_status_id = db.Column(db.Integer, db.ForeignKey('status_of_purchase.id'), nullable=True)

# class Contract(db.Model):
#     __tablename__ = 'contract'
#     id = db.Column(db.Integer, primary_key=True)
#     checklist_id = db.Column(db.Integer, db.ForeignKey('checklist.id'), nullable=True)
#     contract_name = db.Column(db.String, nullable=True)
#     payment_name = db.Column(db.String, nullable=True)
#     contract_ext = db.Column(db.String(32), nullable=True)
#     payment_ext = db.Column(db.String(32), nullable=True)

class KanbanColumn(db.Model):
    __tablename__ = 'kanban_column'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(36), nullable=True)

class Kanban(db.Model):
    __tablename__ = 'kanban'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    column_id = db.Column(db.Integer, db.ForeignKey('kanban_column.id'), nullable=True)
    info = db.Column(db.String, nullable=True)

    kanban_column = db.relationship('KanbanColumn', backref='kanbans')

class Checklist(db.Model):
    __tablename__ = 'checklist'
    id = db.Column(db.Integer, primary_key=True)
    date_of_creation = db.Column(db.DateTime, nullable=True)
    contract_name = db.Column(db.String, nullable=True)
    payment_name = db.Column(db.String, nullable=True)
    contract_ext = db.Column(db.String(32), nullable=True)
    payment_ext = db.Column(db.String(32), nullable=True)

class ChecklistData(db.Model):
    __tablename__ = 'checklist_data'
    id = db.Column(db.Integer, primary_key=True)
    checklist_id = db.Column(db.Integer, db.ForeignKey('checklist.id'), nullable=True)
    description_id = db.Column(db.Integer, db.ForeignKey('description.id'), nullable=True)