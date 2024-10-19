from typing import Protocol


class Extension(Protocol):
    ownerComp: "COMP"
