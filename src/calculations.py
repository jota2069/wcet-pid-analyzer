from collections.abc import Sequence

from .models import Operation, ProcessorModel


def best_case(op: Operation, model: ProcessorModel) -> int:
    """Время операции без промахов кэша и ошибок предсказания."""

    return model.base_cost


def worst_case(op: Operation, model: ProcessorModel) -> int:
    """Время операции при всех предусмотренных штрафах."""

    memory_penalty = op.memory_accesses * model.cache_miss_penalty
    branch_penalty = op.branches * model.branch_miss_penalty
    return model.base_cost + memory_penalty + branch_penalty
