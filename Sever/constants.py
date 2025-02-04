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
    Класс для ID статусов закупок используемых в коде
    """
    REQUEST_TKP = 1
    REQUEST_PROCUREMENT = 2
    APPROVAL = 3
    PLACEMENT_OF_PROCUREMENT = 4
    SUMMING_UP = 5
    CONTRACT_CONCLUDED = 6
    IN_WAREHOUSE = 7

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

SOEForRoles = {
    ConstantRolesID.DEPARTMENT_CHEF_ID: [1, 2, 3, 4, 5, 6],
    ConstantRolesID.MTO_CHEF_ID: [2, 4, 5, 6],
    ConstantRolesID.COMPANY_LEAD_ID: [2, 4, 5, 6],
    ConstantRolesID.EMPLOYEE_ID : [1, 2, 3, 4, 5, 6],
    ConstantRolesID.MTO_EMPLOYEE_ID : [2, 4, 5, 6]
}






