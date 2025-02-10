from enum import Enum

class ConstantRolesID():
    """
    Класс для ID ролей пользователей используемых в коде
    """
    DEPARTMENT_CHEF_ID = 1
    MTO_CHEF_ID = 2
    COMPANY_LEAD_ID = 3
    EMPLOYEE_ID = 4
    MTO_EMPLOYEE_ID = 5

class ConstantSOP():
    """
    Класс для статусов закупок используемых в коде
    """
    NOT_SETTED = 1
    REQUEST_TKP = 2
    REQUEST_PROCUREMENT = 3
    APPROVAL = 4
    PLACEMENT_OF_PROCUREMENT = 5
    SUMMING_UP = 6
    CONTRACT_CONCLUDED = 7
    IN_WAREHOUSE = 8
    PAYMENT = 9

    CONTRACT_TYPE = {
        "Contract": 1,
        "Invoice-contract": 2,
        "Not setted": None
    }
    CONTRACT_TYPE_REVERSE = {
        None: "Не установлен",
        1: "Договор",
        2: "Счет-договор"
    }
    CONTRACT_RULES = {
        CONTRACT_TYPE["Contract"]: [REQUEST_TKP, REQUEST_PROCUREMENT, APPROVAL, PLACEMENT_OF_PROCUREMENT, SUMMING_UP, CONTRACT_CONCLUDED, IN_WAREHOUSE],
        CONTRACT_TYPE["Invoice-contract"]: [REQUEST_TKP, REQUEST_PROCUREMENT, PAYMENT, IN_WAREHOUSE]
    }

class ConstantSOE():
    """
    Класс для ID статусов исполнения используемых в коде
    """
    AWAITING_APPROVAL = 1
    REGISTERED = 2
    DECLINE_BY_DEP_CHEF = 3
    EXECUTION = 4
    COMPLETED = 5
    DECLINE_BY_MTO_CHEF = 6

# Словарь разрешенных статусов по ролям. Формирования словаря по правилам указанных в комментариях к ролям (смотреть БД или читать README)
SOEForRoles = {
    ConstantRolesID.DEPARTMENT_CHEF_ID: [1, 2, 3, 4, 5, 6], 
    ConstantRolesID.MTO_CHEF_ID: [2, 4, 5, 6],
    ConstantRolesID.COMPANY_LEAD_ID: [2, 4, 5, 6],
    ConstantRolesID.EMPLOYEE_ID : [1, 2, 3, 4, 5, 6],
    ConstantRolesID.MTO_EMPLOYEE_ID : [4,5]
}



