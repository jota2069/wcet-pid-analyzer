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


def bcet(fragment: Sequence[Operation], model: ProcessorModel) -> int:
    """Суммарное лучшее время фрагмента."""

    return sum(best_case(operation, model) for operation in fragment)


def wcet(fragment: Sequence[Operation], model: ProcessorModel) -> int:
    """Суммарное худшее время фрагмента."""

    return sum(worst_case(operation, model) for operation in fragment)


def nondeterminism_ratio(
    fragment: Sequence[Operation], model: ProcessorModel
) -> float:
    """Отношение WCET к BCET; при нулевом BCET возвращает бесконечность."""

    best_time = bcet(fragment, model)
    if best_time == 0:
        return float("inf")
    return wcet(fragment, model) / best_time


def source_breakdown(
    fragment: Sequence[Operation], model: ProcessorModel
) -> dict[str, int]:
    """Штрафы памяти и ветвлений в худшем сценарии."""

    memory_accesses = sum(operation.memory_accesses for operation in fragment)
    branches = sum(operation.branches for operation in fragment)
    return {
        "memory": memory_accesses * model.cache_miss_penalty,
        "branches": branches * model.branch_miss_penalty,
    }


def meets_deadline(fragment: Sequence[Operation], model: ProcessorModel) -> bool:
    """Проверка дедлайна по времени худшего сценария."""

    return wcet(fragment, model) <= model.deadline
