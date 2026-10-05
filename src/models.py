from dataclasses import dataclass


@dataclass(frozen=True)
class Operation:
    """Одна укрупнённая операция анализируемого фрагмента."""

    name: str
    type: str
    memory_accesses: int
    branches: int


@dataclass(frozen=True)
class ProcessorModel:
    """Параметры учебной модели процессора в тактах."""

    base_cost: int
    cache_miss_penalty: int
    branch_miss_penalty: int
    deadline: int

