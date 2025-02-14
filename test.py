import requests


base_url = 'http://127.0.0.1:8000'

def login(role):
    url = "http://127.0.0.1:8000/auth/login"
    
    data = {
        "LOGIN": f"test{role}",
        "PASSWORD": "abcd1234"
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=data, headers=headers)
    token = response.json().get("access_token")

    return token

data = {
    "ID_MEMO": 0,
    "DATE_OF_CREATION": "",
    "DATE_OF_APPOINTMENT": "",
    "STATUS_CODE": 0,
    "STATUS_TEXT": "",
    "INFO": "", # Важно
    "JUSTIFICATION": "",
    "HEAD_COMMENT": "",
    "EXECUTOR_COMMENT": "",
    "CREATOR": {
        "ID": 0, # Важно
        "SURNAME": "",
        "NAME": "",
        "PATRONYMIC": "",
        "DEPARTMENT": "",
        "PHONE": "",
        "EMAIL": ""
    },
    "EXECUTOR": {
        "ID": 0,
        "SURNAME": "",
        "NAME": "",
        "PATRONYMIC": "",
        "DEPARTMENT": ""
    },
    "DESCRIPTION": [],
    "JUSTIFICATION_FILE": None
}


def get_desc_dict():
    desc ={
        "ID": 0,
        "POSITION": 1,
        "NAME": "",
        "COUNT": 0,
        "UNIT_CODE": 0,
        "UNIT_TEXT": "",
        "STATUS_CODE": 0,
        "STATUS_TEXT": "",
        "COEF": 0,
        "CONTRACT_INFO": "",
        "DATE_OF_DELIVERY": "",
        "CONTRACT_TYPE": "",
        "EXECUTOR": {
            "ID": None,
            "SURNAME": "",
            "NAME": "г",
            "PATRONYMIC": "",
            "DEPARTMENT": "",
            "PHONE": "",
            "EMAIL": ""
        },
        "HISTORY": []
        }
    return desc
    

# Сценарий 1.
# Добавлении обычной служебки начальником 1 отдела (1)
# Одобрение служебки начальником. (Ха, самоодобрение)
# Одобрение служебки начальником МТО.

def add_1_success():
    token = login(1)
    headers = {"Authorization": f"Bearer {token}"}

    data["INFO"] = "Устранение ошибок в разработке программмы"
    data["CREATOR"]["ID"] = 1
    
    data["DESCRIPTION"].append(get_desc_dict())
    data["DESCRIPTION"][0]["NAME"] = "Транзистор"
    data["DESCRIPTION"][0]["COUNT"] = 100
    data["DESCRIPTION"][0]["UNIT_CODE"] = 6

    data["DESCRIPTION"].append(get_desc_dict())
    data["DESCRIPTION"][1]["NAME"] = "Резистор"
    data["DESCRIPTION"][1]["COUNT"] = 200
    data["DESCRIPTION"][1]["UNIT_CODE"] = 6

    data["DESCRIPTION"].append(get_desc_dict())
    data["DESCRIPTION"][2]["NAME"] = "Реле"
    data["DESCRIPTION"][2]["COUNT"] = 10
    data["DESCRIPTION"][2]["UNIT_CODE"] = 6

    response = requests.post(f"{base_url}/memo/form", headers=headers, json=data)
        
    print("add_1_succes")
    print("================================")
    print(response.status_code)
    print(response.json())
    print("================================")
    return response.json().get("ID")


def accept_1_success(id, role, accept):
    token = login(role)
    headers = {"Authorization": f"Bearer {token}"}

    comment = {"COMMENT": "Заявка подана корректно и нуждается в скорейшем исполнении."}
    response = requests.post(f"{base_url}/memo/accept?id={id}&accept={accept}", headers=headers, json=comment)

    print("accept_1_succes")
    print("================================")
    print(response.status_code)
    print(response.json())
    print("================================")

# def checklist_1_success(memo_id, role):
#     descriptions = Description.query.filter_by(memo_id=memo_id).first()
#     data = [description.id for description in descriptions]

#     token = login(role)
#     headers = {"Authorization": f"Bearer {token}"}
    
#     response = requests.post(f"{base_url}/checklist/create", headers=headers, json=data)



id_memo = add_1_success()
accept_1_success(id_memo, 1, 1)
accept_1_success(id_memo, 2, 0)



# Cценарий 2.
# Добавление обычной служебки сотрудником 1 отдела (4)


# Сценарий 3.
# Добавление обычной служебки начальником 2 отдела (12)



