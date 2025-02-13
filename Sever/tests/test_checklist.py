import pytest
import requests

from Sever import create_app  # Подключаем `create_app`

base_url = 'http://127.0.0.1:8000/checklist'

# Тесты ерунда, т.к. не получается нормально создать экземпляр приложения и тестировать ф-ции.
# Поэтому приходится тестировать http запросы

# При реализации норм тестов добавить следующие штуки
# Проверка данных с разными статусами
# Проверка с разными типами контрактов

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

test_data_full = [{"ID": 170}, {"ID": 171}, {"ID": 172}]
test_data_short = [{"ID": 170}, {"ID": 171}]
test_data_err = [{"ID": 170}, {"ID": 171}, {"ID": 10321321}]

def test_succes_get(client):
    token = login(52)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/get", headers=headers)

    assert response.status_code == 200


def test_create_succes(client):
    token = login(52)
    headers = {"Authorization": f"Bearer {token}"}

    data = {
    "CHECKLIST_ID": 0,
    "VALUES": test_data_full
    }
    response = requests.post(f"{base_url}/create", json=data, headers=headers)
    id = response.json().get("ID")
    assert response.status_code == 200
    # Удаляем дабы не какать в базу
    response = requests.delete(f"{base_url}/delete?id={id}", headers=headers)


def test_create_succes_empty(client):
    token = login(52)
    headers = {"Authorization": f"Bearer {token}"}

    data = {
    "CHECKLIST_ID": 0,
    "VALUES": []
    }
    response = requests.post(f"{base_url}/create", json=data, headers=headers)
    assert response.status_code == 200


def test_create_succes_clear(client):
    token = login(52)
    headers = {"Authorization": f"Bearer {token}"}

    data = {
    "CHECKLIST_ID": 0,
    "VALUES": test_data_full
    }
    response = requests.post(f"{base_url}/create", json=data, headers=headers)
    id = response.json().get("ID")
    
    data = {
    "CHECKLIST_ID": id,
    "VALUES": test_data_short
    }
    response = requests.post(f"{base_url}/create", json=data, headers=headers)
    assert response.status_code == 200

    response = requests.delete(f"{base_url}/delete?id={id}", headers=headers)


def test_create_fail_auth(client):
    token = None
    headers = {"Authorization": f"Bearer {token}"}

    data = {
    "CHECKLIST_ID": 0,
    "VALUES": test_data_full
    }

    response = requests.post(f"{base_url}/create", json=data, headers=headers)
    assert response.status_code == 422


def test_create_fail_incorrect_val(client):
    token = login(52)
    headers = {"Authorization": f"Bearer {token}"}

    data = {
    "CHECKLIST_ID": 0,
    "VALUES": test_data_err
    }

    response = requests.post(f"{base_url}/create", json=data, headers=headers)
    assert response.status_code == 400


def test_create_fail_role_1(client):
    token = login(1)
    headers = {"Authorization": f"Bearer {token}"}

    data = {
    "CHECKLIST_ID": 0,
    "VALUES": test_data_full
    }
    response = requests.post(f"{base_url}/create", json=data, headers=headers)
    id = response.json().get("ID")
    assert response.status_code == 403


def test_create_fail_role_2(client):
    token = login(2)
    headers = {"Authorization": f"Bearer {token}"}

    data = {
    "CHECKLIST_ID": 0,
    "VALUES": test_data_full
    }
    response = requests.post(f"{base_url}/create", json=data, headers=headers)
    id = response.json().get("ID")
    assert response.status_code == 403


def test_create_fail_role_3(client):
    token = login(3)
    headers = {"Authorization": f"Bearer {token}"}

    data = {
    "CHECKLIST_ID": 0,
    "VALUES": test_data_full
    }
    response = requests.post(f"{base_url}/create", json=data, headers=headers)
    id = response.json().get("ID")
    assert response.status_code == 403


def test_create_fail_role_4(client):
    token = login(4)
    headers = {"Authorization": f"Bearer {token}"}

    data = {
    "CHECKLIST_ID": 0,
    "VALUES": test_data_full
    }
    response = requests.post(f"{base_url}/create", json=data, headers=headers)
    id = response.json().get("ID")
    assert response.status_code == 403


def test_create_fail_role_5(client):
    token = login(5)
    headers = {"Authorization": f"Bearer {token}"}

    data = {
    "CHECKLIST_ID": 0,
    "VALUES": test_data_full
    }
    response = requests.post(f"{base_url}/create", json=data, headers=headers)
    id = response.json().get("ID")
    assert response.status_code == 400














