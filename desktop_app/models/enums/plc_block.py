from enum import Enum

class PLCDataType(Enum):
    BOOL = 10
    BYTE = 20
    WORD = 30
    DWORD = 40
    INT = 50
    DINT = 60
    LINT = 70
    REAL = 80
    TIME = 90
    DATE = 100
    TIME_OF_DAY = 110
    CHAR = 120
    DATE_TIME = 130

class PLCDataTypeSize(object):
    BOOL = 1
    BYTE = 1
    WORD = 2
    DWORD = 4
    INT = 2
    DINT = 4
    LINT = 8
    REAL = 4
    TIME = 4
    DATE = 2
    TIME_OF_DAY = 4
    CHAR = 1
    DATE_TIME = 12

class PLCCommandType(Enum):
    PRODUCT_TYPE = 1
    SCAN_NUMBER = 2
    TRIGGER_FLAG = 3
    LIFE_BIT = 4
    TRIGGER_FLAG_ACK = 5
    SCAN_NUMBER_ACK = 6
    SCAN_DONE = 7
    RESULT = 8
    LEARNING_MODE_ENABLE = 9
    LEARNING_MODE_ACK = 10
    PRODUCT_TYPE_ACK = 11
    TEMPLATE_EXIST = 12
    