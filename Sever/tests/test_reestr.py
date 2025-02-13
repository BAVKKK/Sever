import pytest
import requests
import json
from urllib.parse import quote

from Sever import create_app  # Подключаем `create_app`

base_url = 'http://127.0.0.1:8000/reestr'

# Тесты ерунда, т.к. не получается нормально создать экземпляр приложения и тестировать ф-ции.
# Поэтому приходится тестировать http запросы

# При реализации норм тестов добавить следующие штуки

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

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


##############################################################
#=============================================================
#==========ПРОСТЫЕ ТЕСТЫ НА ПОЛУЧЕНИЕ ПО РОЛЯМ================
#=============================================================
##############################################################

def test_succes_get_role_1(client):
    token = login(1)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get", headers=headers)

    assert response.status_code == 200


def test_succes_get_role_2(client):
    token = login(2)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get", headers=headers)

    assert response.status_code == 200


def test_succes_get_role_3(client):
    token = login(3)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get", headers=headers)

    assert response.status_code == 200


def test_succes_get_role_4(client):
    token = login(4)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get", headers=headers)

    assert response.status_code == 200


def test_succes_get_role_5(client):
    token = login(5)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get", headers=headers)

    assert response.status_code == 200


def test_succes_get_role_51(client):
    token = login(51)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get", headers=headers)

    assert response.status_code == 200


def test_succes_get_role_52(client):
    token = login(52)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get", headers=headers)

    assert response.status_code == 200


##############################################################
#=============================================================
#==============ТЕСТЫ ПО РОЛЯМ И СТАТУСАМ======================
#=============================================================
##############################################################

def test_succes_get_role_1_statuses(client):
    token = login(1)
    headers = {"Authorization": f"Bearer {token}"}
    
    for i in range(1,6):
        response = requests.get(f"{base_url}/get?status={i}", headers=headers)
        assert response.status_code == 200


def test_succes_get_role_2_statuses(client):
    token = login(2)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get", headers=headers)

    for i in [2,4,5,6]:
        response = requests.get(f"{base_url}/get?status={i}", headers=headers)
        assert response.status_code == 200


def test_fail_get_role_2_statuses(client):
    token = login(2)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get", headers=headers)

    for i in [1,3]:
        response = requests.get(f"{base_url}/get?status={i}", headers=headers)
        assert response.status_code == 400


def test_succes_get_role_3_statuses(client):
    token = login(3)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get", headers=headers)

    for i in [2,4,5,6]:
        response = requests.get(f"{base_url}/get?status={i}", headers=headers)
        assert response.status_code == 200


def test_fail_get_role_3_statuses(client):
    token = login(3)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get", headers=headers)

    for i in [1,3]:
        response = requests.get(f"{base_url}/get?status={i}", headers=headers)
        assert response.status_code == 400


def test_succes_get_role_4_statuses(client):
    token = login(4)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get", headers=headers)

    for i in range(1,6):
        response = requests.get(f"{base_url}/get?status={i}", headers=headers)
        assert response.status_code == 200


def test_succes_get_role_5_statuses(client):
    token = login(5)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get", headers=headers)

    for i in [4,5]:
        response = requests.get(f"{base_url}/get?status={i}", headers=headers)
        assert response.status_code == 200


def test_fail_get_role_5_statuses(client):
    token = login(5)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get", headers=headers)

    for i in [1,2,3,6]:
        response = requests.get(f"{base_url}/get?status={i}", headers=headers)
        assert response.status_code == 400


# Заведомо не существуюший статус

err_status = 9876543

def test_fail_get_role_1_err_status(client):
    token = login(1)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get?status={err_status}", headers=headers)

    assert response.status_code == 400


def test_fail_get_role_2_err_status(client):
    token = login(2)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get?status={err_status}", headers=headers)

    assert response.status_code == 400


def test_fail_get_role_3_err_status(client):
    token = login(3)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get?status={err_status}", headers=headers)

    assert response.status_code == 400


def test_fail_get_role_4_err_status(client):
    token = login(4)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get?status={err_status}", headers=headers)

    assert response.status_code == 400


def test_fail_get_role_5_err_status(client):
    token = login(5)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get?status={err_status}", headers=headers)

    assert response.status_code == 400


##############################################################
#=============================================================
#==============ТЕСТЫ ПО РОЛЯМ И ФИЛЬТРАМ======================
#=============================================================
##############################################################

##############################################################
#=====================DESCRIPTION=============================
##############################################################

filter_description = quote(json.dumps({"DESCRIPTION": "Проверка"})) # Преобразуем словарь в JSON и кодируем для URL


def test_succes_get_role_1_filt_desc(client):
    token = login(1)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get?filters={filter_description}", headers=headers)

    assert response.status_code == 200


def test_succes_get_role_2_filt_desc(client):
    token = login(2)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get?filters={filter_description}", headers=headers)

    assert response.status_code == 200


def test_succes_get_role_3_filt_desc(client):
    token = login(3)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get?filters={filter_description}", headers=headers)

    assert response.status_code == 200


def test_succes_get_role_4_filt_desc(client):
    token = login(4)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get?filters={filter_description}", headers=headers)

    assert response.status_code == 200


def test_succes_get_role_5_filt_desc(client):
    token = login(5)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get?filters={filter_description}", headers=headers)

    assert response.status_code == 200


##############################################################
#=======================ITEM_NAME=============================
##############################################################

filter_item = quote(json.dumps({"ITEM_NAME": "Соль"})) # Преобразуем словарь в JSON и кодируем для URL


def test_succes_get_role_1_filt_item(client):
    token = login(1)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get?filters={filter_item}", headers=headers)

    assert response.status_code == 200


def test_succes_get_role_2_filt_item(client):
    token = login(2)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get?filters={filter_item}", headers=headers)

    assert response.status_code == 200


def test_succes_get_role_3_filt_item(client):
    token = login(3)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get?filters={filter_item}", headers=headers)

    assert response.status_code == 200


def test_succes_get_role_4_filt_item(client):
    token = login(4)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get?filters={filter_item}", headers=headers)

    assert response.status_code == 200


def test_succes_get_role_5_filt_item(client):
    token = login(5)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get?filters={filter_item}", headers=headers)

    assert response.status_code == 200


##############################################################
#===========================INFO==============================
##############################################################

filter_info = quote(json.dumps({"INFO": "Проверка"})) # Преобразуем словарь в JSON и кодируем для URL


def test_succes_get_role_1_filt_info(client):
    token = login(1)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get?filters={filter_info}", headers=headers)

    assert response.status_code == 200


def test_succes_get_role_2_filt_info(client):
    token = login(2)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get?filters={filter_info}", headers=headers)

    assert response.status_code == 200


def test_succes_get_role_3_filt_info(client):
    token = login(3)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get?filters={filter_info}", headers=headers)

    assert response.status_code == 200


def test_succes_get_role_4_filt_info(client):
    token = login(4)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get?filters={filter_info}", headers=headers)

    assert response.status_code == 200


def test_succes_get_role_5_filt_info(client):
    token = login(5)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get?filters={filter_info}", headers=headers)

    assert response.status_code == 200


##############################################################
#=====================EXECUTOR_NAME===========================
##############################################################

filter_executor = quote(json.dumps({"EXECUTOR_NAME": "Соколова"})) # Преобразуем словарь в JSON и кодируем для URL


def test_succes_get_role_1_filt_exec(client):
    token = login(1)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get?filters={filter_executor}", headers=headers)

    assert response.status_code == 200


def test_succes_get_role_2_filt_exec(client):
    token = login(2)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get?filters={filter_executor}", headers=headers)

    assert response.status_code == 200


def test_succes_get_role_3_filt_exec(client):
    token = login(3)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get?filters={filter_executor}", headers=headers)

    assert response.status_code == 200


def test_succes_get_role_4_filt_exec(client):
    token = login(4)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get?filters={filter_executor}", headers=headers)

    assert response.status_code == 200


def test_succes_get_role_5_filt_exec(client):
    token = login(5)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get?filters={filter_executor}", headers=headers)

    assert response.status_code == 200


##############################################################
#=============================================================
#============ТЕСТЫ ПО РОЛЯМ ФИЛЬТРАМ И СТАТУСАМ===============
#=============================================================
##############################################################


def test_succes_get_role_1_statuses_with_filt(client):
    token = login(1)
    headers = {"Authorization": f"Bearer {token}"}
    
    for i in range(1,6):
        response = requests.get(f"{base_url}/get?status={i}&filters={filter_description}", headers=headers)
        assert response.status_code == 200

        response = requests.get(f"{base_url}/get?status={i}&filters={filter_item}", headers=headers)
        assert response.status_code == 200

        response = requests.get(f"{base_url}/get?status={i}&filters={filter_info}", headers=headers)
        assert response.status_code == 200

        response = requests.get(f"{base_url}/get?status={i}&filters={filter_executor}", headers=headers)
        assert response.status_code == 200


def test_succes_get_role_2_statuses_with_filt(client):
    token = login(2)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get", headers=headers)

    for i in [2,4,5,6]:
        response = requests.get(f"{base_url}/get?status={i}&filters={filter_description}", headers=headers)
        assert response.status_code == 200

        response = requests.get(f"{base_url}/get?status={i}&filters={filter_item}", headers=headers)
        assert response.status_code == 200
        
        response = requests.get(f"{base_url}/get?status={i}&filters={filter_info}", headers=headers)
        assert response.status_code == 200

        response = requests.get(f"{base_url}/get?status={i}&filters={filter_executor}", headers=headers)
        assert response.status_code == 200


def test_fail_get_role_2_statuses_with_filt(client):
    token = login(2)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get", headers=headers)

    for i in [1,3]:
        response = requests.get(f"{base_url}/get?status={i}&filters={filter_description}", headers=headers)
        assert response.status_code == 400

        response = requests.get(f"{base_url}/get?status={i}&filters={filter_item}", headers=headers)
        assert response.status_code == 400
        
        response = requests.get(f"{base_url}/get?status={i}&filters={filter_info}", headers=headers)
        assert response.status_code == 400

        response = requests.get(f"{base_url}/get?status={i}&filters={filter_executor}", headers=headers)
        assert response.status_code == 400


def test_succes_get_role_3_statuses_with_filt(client):
    token = login(3)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get", headers=headers)

    for i in [2,4,5,6]:
        response = requests.get(f"{base_url}/get?status={i}&filters={filter_description}", headers=headers)
        assert response.status_code == 200

        response = requests.get(f"{base_url}/get?status={i}&filters={filter_item}", headers=headers)
        assert response.status_code == 200
        
        response = requests.get(f"{base_url}/get?status={i}&filters={filter_info}", headers=headers)
        assert response.status_code == 200

        response = requests.get(f"{base_url}/get?status={i}&filters={filter_executor}", headers=headers)
        assert response.status_code == 200


def test_fail_get_role_3_statuses_with_filt(client):
    token = login(3)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get", headers=headers)

    for i in [1,3]:
        response = requests.get(f"{base_url}/get?status={i}&filters={filter_description}", headers=headers)
        assert response.status_code == 400

        response = requests.get(f"{base_url}/get?status={i}&filters={filter_item}", headers=headers)
        assert response.status_code == 400
        
        response = requests.get(f"{base_url}/get?status={i}&filters={filter_info}", headers=headers)
        assert response.status_code == 400

        response = requests.get(f"{base_url}/get?status={i}&filters={filter_executor}", headers=headers)
        assert response.status_code == 400


def test_succes_get_role_4_statuses_with_filt(client):
    token = login(4)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get", headers=headers)

    for i in range(1,6):
        response = requests.get(f"{base_url}/get?status={i}&filters={filter_description}", headers=headers)
        assert response.status_code == 200

        response = requests.get(f"{base_url}/get?status={i}&filters={filter_item}", headers=headers)
        assert response.status_code == 200
        
        response = requests.get(f"{base_url}/get?status={i}&filters={filter_info}", headers=headers)
        assert response.status_code == 200

        response = requests.get(f"{base_url}/get?status={i}&filters={filter_executor}", headers=headers)
        assert response.status_code == 200


def test_succes_get_role_5_statuses_with_filt(client):
    token = login(5)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get", headers=headers)

    for i in [4,5]:
        response = requests.get(f"{base_url}/get?status={i}&filters={filter_description}", headers=headers)
        assert response.status_code == 200

        response = requests.get(f"{base_url}/get?status={i}&filters={filter_item}", headers=headers)
        assert response.status_code == 200
        
        response = requests.get(f"{base_url}/get?status={i}&filters={filter_info}", headers=headers)
        assert response.status_code == 200

        response = requests.get(f"{base_url}/get?status={i}&filters={filter_executor}", headers=headers)
        assert response.status_code == 200


def test_fail_get_role_5_statuses_with_filt(client):
    token = login(5)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get", headers=headers)

    for i in [1,2,3,6]:
        response = requests.get(f"{base_url}/get?status={i}&filters={filter_description}", headers=headers)
        assert response.status_code == 400

        response = requests.get(f"{base_url}/get?status={i}&filters={filter_item}", headers=headers)
        assert response.status_code == 400
        
        response = requests.get(f"{base_url}/get?status={i}&filters={filter_info}", headers=headers)
        assert response.status_code == 400

        response = requests.get(f"{base_url}/get?status={i}&filters={filter_executor}", headers=headers)
        assert response.status_code == 400







