from enum import Enum


class DeviceStatus(Enum):
    UNTREATED = "untreated"
    TREATED_BY_A1 = "treated_by_a1"
    TREATED_BY_A2 = "treated_by_a2" 
    TREATED_BY_A3 = "treated_by_a3"
    TREATED_BY_A4 = "treated_by_a4"
    TREATED_BY_A5 = "treated_by_a5"
    TREATED_BY_A6 = "treated_by_a6"
    NOT_FOUND = "not_found"