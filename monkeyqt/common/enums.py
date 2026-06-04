from enum import Enum

class MkType(str, Enum):
    DEFAULT = "default"
    PRIMARY = "primary"
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"
    INFO = "info"

class MkSize(str, Enum):
    LARGE = "large"
    DEFAULT = "default"
    SMALL = "small"
