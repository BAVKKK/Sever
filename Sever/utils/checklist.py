from flask import request, jsonify, Response

import json

from Sever.utils.description import set_sop, drop_sop, set_contract_type
from Sever.db_utils import fill_zeros, DescError, db_create_checklist, add_commit
from Sever.models import *
from Sever.constants import *
from Sever.database.utils import save_file, from_minio_to_b64str
from Sever.database.minio_lib import client


def get_files(cl_id):

    checklist = Checklist.query.filter_by(id=cl_id).first()

    contract = {
        "EXT": None,
        "NAME": None,
        "DATA": None
    }

    payment = {
        "EXT": None,
        "NAME": None,
        "DATA": None
    }
    
    response = {}

    if checklist:
        mime_types = {
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/msword': '.doc',
            'application/pdf': '.pdf',
            'image/jpeg': '.jpeg',
            'image/png': '.png',
            'application/x-zip-compressed': '.zip'
        }
        if checklist.contract_name is not None and checklist.contract_name != "":
            objects = client.list_objects(bucket_name='sever', prefix=f'contracts/{checklist.id}/')
            file = None
            for obj in objects: # Тут цикл потому что не знаю как иначе вытащить обж из "Минио обжекст"
                if obj is not None:
                    file = obj
            if file is not None:
                filename = checklist.contract_name
                minio_id = f"contracts/{checklist.id}/{filename}{mime_types[checklist.contract_ext]}"
                data = f'data:{mime_types[checklist.contract_ext]};base64,{from_minio_to_b64str(minio_id, "sever")}'
                contract["EXT"] = checklist.contract_ext
                contract["DATA"] = data
                contract["NAME"] = checklist.contract_name 
        
        if checklist.payment_name is not None and checklist.payment_name != "":
            objects = client.list_objects(bucket_name='sever', prefix=f'payments/{checklist.id}/')
            file = None
            for obj in objects: # Тут цикл потому что не знаю как иначе вытащить обж из "Минио обжекст"
                if obj is not None:
                    file = obj
            if file is not None:
                filename = checklist.payment_name
                minio_id = f"payments/{checklist.id}/{filename}{mime_types[checklist.payment_ext]}"
                data = f'data:{mime_types[checklist.payment_ext]};base64,{from_minio_to_b64str(minio_id, "sever")}'
                payment["EXT"] = checklist.payment_ext
                payment["DATA"] = data
                payment["NAME"] = checklist.payment_name

    response["CONTRACT"] = contract
    response["PAYMENT"] = payment
    
    return response


def get_desc_for_cl(cl_id):
    try:
        descriptions = db.session.query(Description).join(
                    ChecklistData, ChecklistData.description_id == Description.id
                ).filter(
                    ChecklistData.checklist_id == cl_id
                ).all()
        return descriptions
        
    except Exception as ex:
        raise RuntimeError("Something went wrong.")
        

def create(json_data, cl_id, user_id):
    """
    Метод для создания корзины. 
    При создании корзины статус переводится на запрос ТКП для того чтобы значения пропали из выборки.
    При удалении позиций, ставится предыдущий статус - "Не установлено".
    Данное решение было выбрано для регулирования процесса изменения статуса, дабы не оставлять эту обязанность клиенту.
    """
    try:
        new_cl = False
        if cl_id == 0:
            new_cl = True
            cl_id = db_create_checklist()
        else:
            cl = Checklist.query.filter_by(id=cl_id).first()
            if cl is None:
                raise ValueError(f"Checklist with ID {cl_id} does not exist")

        # Проверка наличия VALUES
        values = json_data.get("VALUES", [])
        if not values:
            # Если передан пустой массив, то удаляем либо только что созданную корзину, либо старую
            # Уменьшаем статусы, если они убраны из корзины
            if new_cl is False:
                descriptions = get_desc_for_cl(cl_id)
                drop_sop(descriptions)

            ChecklistData.query.filter_by(checklist_id=cl_id).delete()
            Checklist.query.filter_by(id=cl_id).delete()
            db.session.commit()
            return jsonify({"STATUS": "Warning", "message": "VALUES list is empty. Checklist has deleted."}), 200

        # Оптимизированная проверка Description
        # Сначала получаем все айдишки
        desc_ids = [i.get("ID") for i in values]
        # Затем проверяем то что их статусы разрешены при создании корзины и проверяем вообще их наличие
        existing_descs = Description.query.filter(
            Description.id.in_(desc_ids),
            Description.status_id.in_([ConstantSOP.NOT_SETTED, ConstantSOP.REQUEST_TKP]),
            Description.id_of_executor == user_id  # Добавляем условие проверки исполнителя
        ).all()

        # Проверяем, все ли ID из desc_ids попали в existing_descs
        if len(desc_ids) != len(existing_descs):
            raise DescError(f"Some Description doesn't exist or have incorret status")
        
        contract_type = None
        for i in existing_descs:
            contract_type = i.contract_type
            if contract_type:
                break

        if new_cl is False:
            # Если чеклист существует, удаляем все записи из ChecklistData для этого чеклиста
            descriptions = get_desc_for_cl(cl_id)
            drop_sop(descriptions)
            descs = [description.id for description in descriptions]
            set_contract_type(None, descs)
            ChecklistData.query.filter_by(checklist_id=cl_id).delete()
            db.session.commit()
        
        if existing_descs[0].status_id == ConstantSOP.NOT_SETTED:
            set_contract_type(contract_type, desc_ids)
            set_sop(desc_ids)

        for i in values:
            id = i.get("ID")
            cld = ChecklistData.query.filter_by(description_id=id).first()
            if cld is not None and cld.checklist_id != cl_id:
                raise DescError(f"""Description with ID {id} is already in ChecklistData""")
            elif cld is None:  # Если запись не найдена, создаем новую
                new_checklist_data = ChecklistData(
                    checklist_id=cl_id,
                    description_id=id
                )
                db.session.add(new_checklist_data)

        db.session.commit()
        return jsonify({"STATUS": "Success", "ID": cl_id}), 200

    except ValueError as ex:
        raise ValueError(f"{ex}")
        
    except DescError as ex:
        # Удаление НОВОГО чеклиста и связанных данных при ошибке
        if new_cl is True:
            ChecklistData.query.filter_by(checklist_id=cl_id).delete()
            Checklist.query.filter_by(id=cl_id).delete()
            db.session.commit()
        raise ValueError(f"{ex}")

    except Exception as ex:
        db.session.rollback()  # Откатываем транзакцию в случае ошибки
        raise RuntimeError(f"{ex}")


def get(user_id):
    try:
        # Запрос в базу данных
        query_result = db.session.query(
            ChecklistData.checklist_id,
            Description.id,
            Description.name,
            Description.memo_id,
            Description.count,
            StatusOfPurchase.name,
            Description.contract_type,
            Units.short_name,
            Units.full_name,
            Checklist.date_of_creation
        ).join(Checklist, Checklist.id == ChecklistData.checklist_id
        ).join(Description, Description.id == ChecklistData.description_id
        ).join(Units, Units.id == Description.unit_id
        ).join(StatusOfPurchase, StatusOfPurchase.id == Description.status_id
        ).filter(Description.id_of_executor == user_id).all()

        # Группируем данные по CHECKLIST_ID
        checklist_data = {}
        checklist_info = {}
        for checklist_id, description_id, description_name, memo_id, count, status_name, contract_type, unit_short_name, unit_full_name, checklist_date_of_creation in query_result:
            if checklist_id not in checklist_data:
                checklist_data[checklist_id] = []
                checklist_info[checklist_id] = {"STATUS": status_name, "CONTRACT_TYPE": contract_type, "DATE_OF_CREATION": checklist_date_of_creation.strftime("%Y-%m-%d")}
            
            checklist_data[checklist_id].append({
                "ID": description_id,
                "NAME": description_name,
                "MEMO_ID": fill_zeros(memo_id),
                "COUNT": count,
                "UNIT_SHORT_NAME": unit_short_name,
                "UNIT_FULL_NAME": unit_full_name,
            })

        # Формируем список всех чек-листов
        response = []
        for cl_id, values in checklist_data.items():
            files = get_files(cl_id)
            data = {
                "CHECKLIST_ID": cl_id,
                "STATUS": checklist_info[cl_id]["STATUS"],
                "DATE_OF_CREATION": checklist_info[cl_id]["DATE_OF_CREATION"],
                "CONTRACT_TYPE": ConstantSOP.CONTRACT_TYPE_REVERSE[checklist_info[cl_id]["CONTRACT_TYPE"]],
                "VALUES": values,
                "CONTRACT": files["CONTRACT"],
                "PAYMENT": files["PAYMENT"]
            }

            response.append(data)

        json_response = json.dumps(response, ensure_ascii=False, indent=4)
        return Response(json_response, content_type='application/json; charset=utf-8')

    except Exception as ex:
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500


def delete(cl_id):
    try:
        # Получаем все связанные Description
        descriptions = get_desc_for_cl(cl_id)

        if not descriptions:
            raise ValueError("Checklist not found")

        # Проверяем условия удаления
        first_desc = descriptions[0]
        if first_desc.contract_type is None or (
            first_desc.status_id == ConstantSOP.NOT_SETTED) or (
            first_desc.status_id in ConstantSOP.CONTRACT_RULES[first_desc.contract_type] and
            first_desc.status_id == ConstantSOP.CONTRACT_RULES[first_desc.contract_type][0]
        ):
            # Сбрасываем статусы у всех связанных Description
            drop_sop(descriptions)
            descs = [description.id for description in descriptions]
            set_contract_type(None, descs)

            # Удаляем данные
            ChecklistData.query.filter_by(checklist_id=cl_id).delete()
            Checklist.query.filter_by(id=cl_id).delete()
            db.session.commit()

            return jsonify({"msg": "Checklist deleted successfully"}), 200
        else:
            return jsonify({"msg": "Pozdnyak metatsya"}), 200

    except Exception as ex:
        db.session.rollback()
        return jsonify({"STATUS": "Error", "message": str(ex)}), 500


def add_contract_file(data):
    """
    Добавляем файл контракта или счета на оплату в базу и загружаем на сервер
    Модель такого вида:
    {
        "CHECKLIST_ID": 0,
        "IS_CONTRACT": 0, # 0 | 1 - Счёт на оплату/Договор
        "FILE": {
            "NAME": "",
            "EXT": "",
            "DATA: ""
        }
    }
    """
    try:
        cl_id = data.get("CHECKLIST_ID")
        is_contract = data.get("IS_CONTRACT")
        folder = None

        if cl_id is None or cl_id < 1:
            raise ValueError("Checklist id is incorrect")
        
        if is_contract is None or is_contract not in [0,1]:
            raise ValueError("Is contract valuer is incorrect")
        else:
            folder = "contracts" if is_contract else "payments"

        if "FILE" in data and data["FILE"] is not None:
            save_file(checklist_id=cl_id, data=data["FILE"], folder=folder)
        else:
            raise ValueError("File does not exist")
        
        checklist = Checklist.query.filter_by(id=cl_id).first()

        if is_contract:
            checklist.contract_name = data["FILE"]["NAME"]
            checklist.contract_ext = data["FILE"]["EXT"]
        else:
            checklist.payment_name = data["FILE"]["NAME"]
            checklist.payment_ext = data["FILE"]["EXT"]

        add_commit(checklist)

        return jsonify({"STATUS": "Success", "CHECKLIST_ID": cl_id}), 200 
    
    except ValueError as ex:
        db.session.rollback()
        raise ValueError(f"{ex}")
    
    except Exception as ex:
        db.session.rollback()
        raise RuntimeError(f"{ex}")
