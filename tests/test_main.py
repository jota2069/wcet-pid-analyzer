import json
from pathlib import Path

from src.main import build_report, main
from src.models import Operation, ProcessorModel


def test_build_report_contains_table_and_summary() -> None:
    model = ProcessorModel(1, 20, 10, 100)
    fragment = [Operation("Чтение уставки", "чтение", 1, 0)]

    report = build_report(fragment, model)

    assert "| Операция" in report
    assert "| Тип" in report
    assert "| Лучшее" in report
    assert "| Худшее" in report
    assert "BCET: 1 тактов" in report
    assert "WCET: 21 тактов" in report
    assert "Вклад памяти: 20 тактов" in report
    assert "Вклад ветвлений: 0 тактов" in report
    assert "Дедлайн соблюдается" in report


def test_build_report_marks_missed_deadline() -> None:
    model = ProcessorModel(1, 20, 10, 20)
    fragment = [Operation("Чтение уставки", "чтение", 1, 0)]

    assert "Дедлайн не соблюдается" in build_report(fragment, model)


def test_main_loads_json_and_prints_report(tmp_path: Path, capsys) -> None:
    processor_path = tmp_path / "processor.json"
    fragment_path = tmp_path / "fragment.json"
    processor_path.write_text(
        json.dumps(
            {
                "base_cost": 1,
                "cache_miss_penalty": 20,
                "branch_miss_penalty": 10,
                "deadline": 100,
            }
        ),
        encoding="utf-8",
    )
    fragment_path.write_text(
        json.dumps(
            {
                "operations": [
                    {
                        "name": "Запись на привод",
                        "type": "запись",
                        "memory_accesses": 1,
                        "branches": 0,
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    exit_code = main(
        ["--processor", str(processor_path), "--fragment", str(fragment_path)]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Запись на привод" in captured.out
    assert "WCET: 21 тактов" in captured.out
    assert captured.err == ""


def test_main_returns_error_for_missing_input(tmp_path: Path, capsys) -> None:
    exit_code = main(["--processor", str(tmp_path / "missing.json")])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Ошибка входных данных" in captured.err
