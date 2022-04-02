from enum import Enum, auto

class CloudType(Enum):
    ORIGINAL = auto()
    PROCESSED = auto()
    CLUSTERED = auto()
    CLUSTERED_MODIFIED = auto()
    RESULT = auto()


