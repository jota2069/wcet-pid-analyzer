import math

import pytest

from src.calculations import (
    bcet,
    best_case,
    meets_deadline,
    nondeterminism_ratio,
    source_breakdown,
    wcet,
    worst_case,
)
from src.models import Operation, ProcessorModel


def make_model(deadline: int = 100) -> ProcessorModel:
    return ProcessorModel(
        base_cost=2,
        cache_miss_penalty=5,
        branch_miss_penalty=7,
        deadline=deadline,
    )


def test_best_case_uses_only_base_cost() -> None:
    operation = Operation("Проверка", "ветвление", memory_accesses=3, branches=2)

    assert best_case(operation, make_model()) == 2


def test_worst_case_adds_memory_and_branch_penalties() -> None:
    operation = Operation("Проверка", "ветвление", memory_accesses=3, branches=2)

    assert worst_case(operation, make_model()) == 2 + 3 * 5 + 2 * 7


def test_bcet_sums_best_times_for_all_operations() -> None:
    fragment = [
        Operation("Чтение", "чтение", 1, 0),
        Operation("Вычисление", "арифметика", 0, 0),
        Operation("Запись", "запись", 1, 0),
    ]

    assert bcet(fragment, make_model()) == 6


def test_wcet_sums_worst_times_for_all_operations() -> None:
    fragment = [
        Operation("Чтение", "чтение", 1, 0),
        Operation("Ограничение", "ветвление", 0, 2),
    ]

    assert wcet(fragment, make_model()) == 4 + 5 + 14


def test_nondeterminism_ratio_is_wcet_divided_by_bcet() -> None:
    fragment = [Operation("Чтение", "чтение", 1, 0)]

    assert nondeterminism_ratio(fragment, make_model()) == pytest.approx(3.5)


def test_nondeterminism_ratio_handles_zero_bcet() -> None:
    model = ProcessorModel(0, 5, 7, 100)
    fragment = [Operation("Чтение", "чтение", 1, 0)]

    assert math.isinf(nondeterminism_ratio(fragment, model))


def test_source_breakdown_separates_memory_and_branches() -> None:
    fragment = [
        Operation("Чтение", "чтение", 2, 0),
        Operation("Ограничение", "ветвление", 0, 3),
    ]

    assert source_breakdown(fragment, make_model()) == {
        "memory": 10,
        "branches": 21,
    }


@pytest.mark.parametrize(
    ("deadline", "expected"),
    [(6, False), (7, True), (8, True)],
)
def test_meets_deadline_checks_wcet_boundary(deadline: int, expected: bool) -> None:
    fragment = [Operation("Чтение", "чтение", 1, 0)]

    assert meets_deadline(fragment, make_model(deadline)) is expected


def test_methodical_example_has_expected_results() -> None:
    model = ProcessorModel(
        base_cost=1,
        cache_miss_penalty=20,
        branch_miss_penalty=10,
        deadline=100,
    )
    fragment = [Operation(f"Операция {index}", "тест", 0, 0) for index in range(8)]
    fragment[0] = Operation("Чтение 1", "чтение", 1, 0)
    fragment[1] = Operation("Чтение 2", "чтение", 1, 0)
    fragment[2] = Operation("Чтение 3", "чтение", 1, 0)
    fragment[3] = Operation("Проверка 1", "ветвление", 0, 1)
    fragment[4] = Operation("Проверка 2", "ветвление", 0, 1)

    assert bcet(fragment, model) == 8
    assert wcet(fragment, model) == 88
    assert nondeterminism_ratio(fragment, model) == 11
    assert source_breakdown(fragment, model) == {
        "memory": 60,
        "branches": 20,
    }
    assert meets_deadline(fragment, model) is True
