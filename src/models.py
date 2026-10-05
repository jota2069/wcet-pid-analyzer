from dataclasses import dataclass


def _validate_non_negative_int(value: object, field_name: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} должно быть целым неотрицательным числом")


@dataclass(frozen=True)
class Operation:
    """Одна укрупнённая операция анализируемого фрагмента."""

    name: str
    type: str
    memory_accesses: int
    branches: int

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name должно быть непустой строкой")
        if not isinstance(self.type, str) or not self.type.strip():
            raise ValueError("type должно быть непустой строкой")
        _validate_non_negative_int(self.memory_accesses, "memory_accesses")
        _validate_non_negative_int(self.branches, "branches")


@dataclass(frozen=True)
class ProcessorModel:
    """Параметры учебной модели процессора в тактах."""

    base_cost: int
    cache_miss_penalty: int
    branch_miss_penalty: int
    deadline: int

    def __post_init__(self) -> None:
        _validate_non_negative_int(self.base_cost, "base_cost")
        _validate_non_negative_int(
            self.cache_miss_penalty, "cache_miss_penalty"
        )
        _validate_non_negative_int(
            self.branch_miss_penalty, "branch_miss_penalty"
        )
        _validate_non_negative_int(self.deadline, "deadline")
