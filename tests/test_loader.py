import json
from pathlib import Path

import pytest

from src.loader import InputDataError, load_fragment, load_processor
from src.models import Operation, ProcessorModel


def write_json(path: Path, data: object) -> Path:
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def test_load_processor_reads_json_file(tmp_path: Path) -> None:
    path = write_json(
        tmp_path / "processor.json",
        {
            "base_cost": 2,
            "cache_miss_penalty": 12,
            "branch_miss_penalty": 6,
            "deadline": 100,
        },
    )

    assert load_processor(path) == ProcessorModel(2, 12, 6, 100)


def test_load_fragment_reads_operations_from_json(tmp_path: Path) -> None:
    path = write_json(
        tmp_path / "fragment.json",
        {
            "operations": [
                {
                    "name": "Чтение уставки",
                    "type": "чтение",
                    "memory_accesses": 1,
                    "branches": 0,
                }
            ]
        },
    )

    assert load_fragment(path) == [Operation("Чтение уставки", "чтение", 1, 0)]


def test_load_processor_rejects_negative_value(tmp_path: Path) -> None:
    path = write_json(
        tmp_path / "processor.json",
        {
            "base_cost": -1,
            "cache_miss_penalty": 12,
            "branch_miss_penalty": 6,
            "deadline": 100,
        },
    )

    with pytest.raises(InputDataError, match="base_cost"):
        load_processor(path)


def test_load_processor_rejects_boolean_instead_of_integer(tmp_path: Path) -> None:
    path = write_json(
        tmp_path / "processor.json",
        {
            "base_cost": True,
            "cache_miss_penalty": 12,
            "branch_miss_penalty": 6,
            "deadline": 100,
        },
    )

    with pytest.raises(InputDataError, match="base_cost"):
        load_processor(path)


def test_load_fragment_rejects_empty_operation_list(tmp_path: Path) -> None:
    path = write_json(tmp_path / "fragment.json", {"operations": []})

    with pytest.raises(InputDataError, match="непустым списком"):
        load_fragment(path)


def test_load_fragment_identifies_invalid_operation(tmp_path: Path) -> None:
    path = write_json(
        tmp_path / "fragment.json",
        {
            "operations": [
                {
                    "name": "",
                    "type": "чтение",
                    "memory_accesses": 1,
                    "branches": 0,
                }
            ]
        },
    )

    with pytest.raises(InputDataError, match="операция 1"):
        load_fragment(path)


@pytest.mark.parametrize(
    ("field", "value"),
    [("memory_accesses", -1), ("branches", -1)],
)
def test_load_fragment_rejects_negative_counters(
    tmp_path: Path, field: str, value: int
) -> None:
    operation = {
        "name": "Операция",
        "type": "тест",
        "memory_accesses": 0,
        "branches": 0,
    }
    operation[field] = value
    path = write_json(tmp_path / "fragment.json", {"operations": [operation]})

    with pytest.raises(InputDataError, match=field):
        load_fragment(path)


def test_loader_rejects_malformed_json(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text('{"base_cost":', encoding="utf-8")

    with pytest.raises(InputDataError, match="Некорректный JSON"):
        load_processor(path)


def test_loader_rejects_non_object_json_root(tmp_path: Path) -> None:
    path = write_json(tmp_path / "processor.json", [1, 2, 3])

    with pytest.raises(InputDataError, match="должен быть объектом JSON"):
        load_processor(path)


def test_loader_reports_missing_file(tmp_path: Path) -> None:
    with pytest.raises(InputDataError, match="Не удалось прочитать файл"):
        load_fragment(tmp_path / "missing.json")
