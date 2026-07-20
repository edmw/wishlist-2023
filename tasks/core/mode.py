from enum import StrEnum


class Mode(StrEnum):
    DEVELOP = "develop"
    DEVELOP_DEBUG = "develop_debug"
    PRODUCTION = "deploy"
