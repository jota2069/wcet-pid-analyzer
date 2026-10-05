import json
from pathlib import Path
from typing import Any

from .models import Operation, ProcessorModel


class InputDataError(ValueError):
    """Ошибка чтения или проверки входных данных."""


def _read_json(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    try:
        with file_path.open(encoding="utf-8") as file:
            data = json.load(file)
    except OSError as error:
        raise InputDataError(f"Не удалось прочитать файл {file_path}: {error}") from error
    except json.JSONDecodeError as error:
        raise InputDataError(
            f"Некорректный JSON в файле {file_path}: строка {error.lineno}"
        ) from error

    if not isinstance(data, dict):
        raise InputDataError(f"Корень файла {file_path} должен быть объектом JSON")
    return data


def load_processor(path: str | Path) -> ProcessorModel:
    data = _read_json(path)
    try:
        return ProcessorModel(**data)
    except (TypeError, ValueError) as error:
        raise InputDataError(f"Некорректная модель процессора: {error}") from error


def load_fragment(path: str | Path) -> list[Operation]:
    data = _read_json(path)
    operations_data = data.get("operations")
    if not isinstance(operations_data, list) or not operations_data:
        raise InputDataError("Поле operations должно быть непустым списком")

    operations = []
    for index, operation_data in enumerate(operations_data, start=1):
        if not isinstance(operation_data, dict):
            raise InputDataError(f"Операция {index} должна быть объектом JSON")
        try:
            operations.append(Operation(**operation_data))
        except (TypeError, ValueError) as error:
            raise InputDataError(f"Некорректная операция {index}: {error}") from error
    return operations
