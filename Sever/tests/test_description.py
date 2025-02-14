import pytest
import requests

from Sever import create_app  # Подключаем `create_app`

base_url = 'http://127.0.0.1:8000/desc'

# Тесты ерунда, т.к. не получается нормально создать экземпляр приложения и тестировать ф-ции.
# Поэтому приходится тестировать http запросы


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

logins_correct = [2, 5, 51, 52]
logins_incorrect = [1,3,4]

statuses = [1,2,3,4,5,6]
status_incorrect = 9999999

##############################################################
#=============================================================
#======================ТЕСТЫ ПО РОЛЯМ=========================
#=============================================================
##############################################################

def test_succes_get_aggr_roles(client):
    for id in logins_correct:
        token = login(id)
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{base_url}/get_aggregate", headers=headers)

        assert response.status_code == 200


def test_fail_get_aggr_roles(client):
    for id in logins_incorrect:
        token = login(id)
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{base_url}/get_aggregate", headers=headers)

        assert response.status_code == 403

##############################################################
#=============================================================
#=================ТЕСТЫ ПО РОЛЯМ  И СТАТУСАМ==================
#=============================================================
##############################################################

def test_succes_get_aggr_roles_statuses(client):
    for id in logins_correct:
        for status in statuses:
            token = login(id)
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{base_url}/get_aggregate?status={status}", headers=headers)

            assert response.status_code == 200


def test_fail_get_aggr_roles_statuses(client):
    for id in logins_correct:
        token = login(id)
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{base_url}/get_aggregate?status={status_incorrect}", headers=headers)

        assert response.status_code == 400
