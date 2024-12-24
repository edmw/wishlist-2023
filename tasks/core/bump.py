from enum import StrEnum


class Bump(StrEnum):
    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"
