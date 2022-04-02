from enum import Enum


class ProductType(Enum):
    FMB010 = 1
    FMB110 = 2
    FM_NO_RECORD = 3
    FMB600 = 4
    FMB920 = 5
    FMB910 = 6
    BTS = 7


class ProcessingStrategy(Enum):
    CLUSTERING = 10
    BOUNDING_BOX = 20
    ZONE_STATISTICS = 30


class ReferenceType(Enum):
    AUTO = 10
    MANUAL = 20
