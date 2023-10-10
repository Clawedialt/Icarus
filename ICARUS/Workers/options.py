import io
from typing import Any


class Option:
    __slots__ = ["name", "value", "description", "option_type"]

    def __init__(self, name: str, value: Any, description: str, option_type: Any) -> None:
        self.name = name
        self.value = value
        self.description: str = description
        self.option_type = option_type

    def __getstate__(self) -> tuple[str, Any, str]:
        return (self.name, self.value, self.description)

    def __setstate__(self, state: tuple[str, Any, str]) -> None:
        self.name, self.value, self.description = state

    def __str__(self) -> str:
        ss = io.StringIO()

        ss.write(f"{self.name} : {self.value}\n")
        ss.write(f"{self.description}\n")
        return ss.getvalue()

    def __repr__(self) -> str:
        ss = io.StringIO()

        ss.write(f"{self.name} : {self.value}\n")
        ss.write(f"{self.description}\n")
        return ss.getvalue()
