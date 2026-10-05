import math
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

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
from .main import DEFAULT_FRAGMENT, DEFAULT_PROCESSOR
from .models import Operation, ProcessorModel


class WcetApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Анализатор WCET шага ПИД-регулятора")
        self.geometry("1050x700")
        self.minsize(900, 620)

        self.model: ProcessorModel | None = None
        self.fragment: list[Operation] = []
        self.processor_path = Path(DEFAULT_PROCESSOR)
        self.fragment_path = Path(DEFAULT_FRAGMENT)
        self.processor_path_value = tk.StringVar(value="Файл не выбран")
        self.fragment_path_value = tk.StringVar(value="Файл не выбран")

        self.parameter_values = {
            name: tk.StringVar(value="—")
            for name in (
                "base_cost",
                "cache_miss_penalty",
                "branch_miss_penalty",
                "deadline",
            )
        }
        self.result_values = {
            name: tk.StringVar(value="—")
            for name in ("bcet", "wcet", "ratio", "memory", "branches")
        }
        self.status_value = tk.StringVar(value="Расчёт не выполнен")

        self._configure_style()
        self._build_layout()
        self._load_defaults()

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.configure("Treeview", rowheight=27)
        style.configure("Heading.TLabel", font=("TkDefaultFont", 11, "bold"))

    def _build_layout(self) -> None:
        container = ttk.Frame(self, padding=16)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="Оценка времени выполнения шага ПИД-регулятора",
            style="Heading.TLabel",
        ).pack(anchor="w", pady=(0, 12))

        files = ttk.LabelFrame(container, text="Входные файлы", padding=10)
        files.pack(fill="x", pady=(0, 12))
        ttk.Button(
            files,
            text="Выбрать модель процессора",
            command=self._select_processor,
        ).grid(row=0, column=0, padx=(0, 10), pady=3, sticky="w")
        ttk.Label(files, textvariable=self.processor_path_value).grid(
            row=0, column=1, sticky="w"
        )
        ttk.Button(
            files,
            text="Выбрать фрагмент операций",
            command=self._select_fragment,
        ).grid(row=1, column=0, padx=(0, 10), pady=3, sticky="w")
        ttk.Label(files, textvariable=self.fragment_path_value).grid(
            row=1, column=1, sticky="w"
        )

        parameters = ttk.LabelFrame(container, text="Модель процессора", padding=10)
        parameters.pack(fill="x", pady=(0, 12))
        labels = {
            "base_cost": "Базовая стоимость",
            "cache_miss_penalty": "Штраф промаха кэша",
            "branch_miss_penalty": "Штраф ветвления",
            "deadline": "Дедлайн",
        }
        for column, (name, label) in enumerate(labels.items()):
            block = ttk.Frame(parameters)
            block.grid(row=0, column=column, padx=12, sticky="w")
            ttk.Label(block, text=label).pack(anchor="w")
            ttk.Label(block, textvariable=self.parameter_values[name]).pack(anchor="w")

        operations = ttk.LabelFrame(container, text="Операции", padding=10)
        operations.pack(fill="both", expand=True, pady=(0, 12))
        columns = ("name", "type", "memory", "branches", "bcet", "wcet")
        self.table = ttk.Treeview(operations, columns=columns, show="headings")
        headings = {
            "name": "Имя операции",
            "type": "Тип",
            "memory": "Память",
            "branches": "Ветвления",
            "bcet": "BCET",
            "wcet": "WCET",
        }
        widths = {
            "name": 310,
            "type": 120,
            "memory": 85,
            "branches": 90,
            "bcet": 70,
            "wcet": 70,
        }
        for name in columns:
            self.table.heading(name, text=headings[name])
            self.table.column(name, width=widths[name], anchor="center")
        self.table.column("name", anchor="w")
        self.table.column("type", anchor="w")

        scrollbar = ttk.Scrollbar(operations, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        results = ttk.LabelFrame(container, text="Результаты", padding=10)
        results.pack(fill="x")
        result_labels = {
            "bcet": "BCET",
            "wcet": "WCET",
            "ratio": "Коэффициент",
            "memory": "Вклад памяти",
            "branches": "Вклад ветвлений",
        }
        for column, (name, label) in enumerate(result_labels.items()):
            block = ttk.Frame(results)
            block.grid(row=0, column=column, padx=10, sticky="w")
            ttk.Label(block, text=label).pack(anchor="w")
            ttk.Label(block, textvariable=self.result_values[name]).pack(anchor="w")

        self.status_label = tk.Label(
            results, textvariable=self.status_value, font=("TkDefaultFont", 10, "bold")
        )
        self.status_label.grid(row=1, column=0, columnspan=5, padx=10, pady=(12, 0))

        ttk.Button(container, text="Рассчитать", command=self.calculate).pack(
            anchor="e", pady=(12, 0)
        )

    def _load_defaults(self) -> None:
        try:
            self.model = load_processor(self.processor_path)
            self.fragment = load_fragment(self.fragment_path)
            self._update_file_labels()
            self._refresh_view()
            self.calculate()
        except InputDataError as error:
            messagebox.showerror("Ошибка входных данных", str(error))

    def _select_processor(self) -> None:
        selected = filedialog.askopenfilename(
            title="Выберите модель процессора",
            filetypes=(("JSON-файлы", "*.json"), ("Все файлы", "*.*")),
        )
        if not selected:
            return
        try:
            model = load_processor(selected)
        except InputDataError as error:
            messagebox.showerror("Ошибка входных данных", str(error))
            return
        self.model = model
        self.processor_path = Path(selected)
        self._update_file_labels()
        self._refresh_view()
        self.calculate()

    def _select_fragment(self) -> None:
        selected = filedialog.askopenfilename(
            title="Выберите описание фрагмента",
            filetypes=(("JSON-файлы", "*.json"), ("Все файлы", "*.*")),
        )
        if not selected:
            return
        try:
            fragment = load_fragment(selected)
        except InputDataError as error:
            messagebox.showerror("Ошибка входных данных", str(error))
            return
        self.fragment = fragment
        self.fragment_path = Path(selected)
        self._update_file_labels()
        self._refresh_view()
        self.calculate()

    def _update_file_labels(self) -> None:
        processor_text = (
            f"Модель: {self.processor_path.name}"
            if self.model is not None
            else "Файл не выбран"
        )
        fragment_text = (
            f"Фрагмент: {self.fragment_path.name}"
            if self.fragment
            else "Файл не выбран"
        )
        self.processor_path_value.set(processor_text)
        self.fragment_path_value.set(fragment_text)

    def _refresh_view(self) -> None:
        if self.model is None:
            return
        for name, value in self.parameter_values.items():
            value.set(str(getattr(self.model, name)))
        self.table.delete(*self.table.get_children())
        for operation in self.fragment:
            self.table.insert(
                "",
                "end",
                values=(
                    operation.name,
                    operation.type,
                    operation.memory_accesses,
                    operation.branches,
                    best_case(operation, self.model),
                    worst_case(operation, self.model),
                ),
            )

    def calculate(self) -> None:
        if self.model is None or not self.fragment:
            messagebox.showwarning("Нет данных", "Сначала загрузите входные данные")
            return

        ratio = nondeterminism_ratio(self.fragment, self.model)
        breakdown = source_breakdown(self.fragment, self.model)
        values = {
            "bcet": f"{bcet(self.fragment, self.model)} тактов",
            "wcet": f"{wcet(self.fragment, self.model)} тактов",
            "ratio": "∞" if math.isinf(ratio) else f"{ratio:.2f}",
            "memory": f"{breakdown['memory']} тактов",
            "branches": f"{breakdown['branches']} тактов",
        }
        for name, text in values.items():
            self.result_values[name].set(text)

        if meets_deadline(self.fragment, self.model):
            self.status_value.set("Дедлайн соблюдается")
            self.status_label.configure(fg="#1b6e2d")
        else:
            self.status_value.set("Дедлайн не соблюдается")
            self.status_label.configure(fg="#a32626")


def main() -> None:
    WcetApp().mainloop()


if __name__ == "__main__":
    main()
