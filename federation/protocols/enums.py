import typing

from enum_properties import IntEnumProperties, Symmetric

class ProtocolType(IntEnumProperties):
    string: typing.Annotated[str, Symmetric(case_fold=True)]

    ACTIVITYPUB = 0, "activitypub"
    DIASPORA = 1, "diaspora"
    MATRIX = 2, "matrix"
