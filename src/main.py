import argparse
import math
import sys
from collections.abc import Sequence
from pathlib import Path

from .calculations import (
    bcet,
    best_case,
    meets_deadline,
    nondeterminism_ratio,
    source_breakdown,
    wcet,
    worst_case,
)
from .loader import InputDataError, load_fragment, load_processor
from .models import Operation, ProcessorModel


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROCESSOR = PROJECT_ROOT / "data" / "processor.json"
DEFAULT_FRAGMENT = PROJECT_ROOT / "data" / "fragment.json"


def _format_table(rows: list[list[str]]) -> str:
    widths = [max(len(row[index]) for row in rows) for index in range(len(rows[0]))]
    separator = "+-" + "-+-".join("-" * width for width in widths) + "-+"

    lines = [separator]
    for index, row in enumerate(rows):
        cells = [value.ljust(widths[column]) for column, value in enumerate(row)]
        lines.append("| " + " | ".join(cells) + " |")
        if index == 0:
            lines.append(separator)
    lines.append(separator)
    return "\n".join(lines)


def build_report(fragment: Sequence[Operation], model: ProcessorModel) -> str:
    rows = [["Операция", "Тип", "Лучшее", "Худшее"]]
    rows.extend(
        [
            operation.name,
            operation.type,
            str(best_case(operation, model)),
            str(worst_case(operation, model)),
        ]
        for operation in fragment
    )

    best_time = bcet(fragment, model)
    worst_time = wcet(fragment, model)
    ratio = nondeterminism_ratio(fragment, model)
    breakdown = source_breakdown(fragment, model)
    ratio_text = "∞" if math.isinf(ratio) else f"{ratio:.2f}"
    deadline_status = (
        "Дедлайн соблюдается" if meets_deadline(fragment, model)
        else "Дедлайн не соблюдается"
    )

    summary = [
        f"BCET: {best_time} тактов",
        f"WCET: {worst_time} тактов",
        f"Коэффициент недетерминизма: {ratio_text}",
        f"Вклад памяти: {breakdown['memory']} тактов",
        f"Вклад ветвлений: {breakdown['branches']} тактов",
        f"Дедлайн: {model.deadline} тактов",
        deadline_status,
    ]
    return f"{_format_table(rows)}\n\n" + "\n".join(summary)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Оценка BCET и WCET одного шага ПИД-регулятора"
    )
    parser.add_argument(
        "--processor",
        type=Path,
        default=DEFAULT_PROCESSOR,
        help="путь к JSON-файлу модели процессора",
    )
    parser.add_argument(
        "--fragment",
        type=Path,
        default=DEFAULT_FRAGMENT,
        help="путь к JSON-файлу операций фрагмента",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    try:
        model = load_processor(args.processor)
        fragment = load_fragment(args.fragment)
    except InputDataError as error:
        print(f"Ошибка входных данных: {error}", file=sys.stderr)
        return 1

    print(build_report(fragment, model))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
