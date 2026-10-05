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
        self.geometry("1140x800")
        self.minsize(940, 700)
        self.configure(background="#f3f4f6")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

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
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure(
            ".",
            font=("TkDefaultFont", 10),
            background="#f3f4f6",
            foreground="#26323d",
        )
        style.configure("TFrame", background="#f3f4f6")
        style.configure("TLabel", background="#f3f4f6")
        style.configure(
            "Title.TLabel",
            font=("TkDefaultFont", 18, "bold"),
            foreground="#1f2a35",
        )
        style.configure("Subtitle.TLabel", foreground="#65717c")
        style.configure(
            "Section.TLabelframe",
            background="#ffffff",
            bordercolor="#d6dbe1",
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "Section.TLabelframe.Label",
            font=("TkDefaultFont", 10, "bold"),
            background="#f3f4f6",
            foreground="#34414d",
        )
        style.configure("Section.TFrame", background="#ffffff")
        style.configure("Section.TLabel", background="#ffffff")
        style.configure(
            "Value.TLabel",
            background="#ffffff",
            font=("TkDefaultFont", 11, "bold"),
            foreground="#26323d",
        )
        style.configure("File.TLabel", background="#ffffff", foreground="#53606c")
        style.configure("TButton", padding=(12, 7))
        style.configure(
            "Accent.TButton",
            padding=(18, 8),
            font=("TkDefaultFont", 10, "bold"),
            background="#4d6075",
            foreground="#ffffff",
            bordercolor="#4d6075",
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#405268"), ("pressed", "#35475b")],
        )
        style.configure(
            "Treeview",
            rowheight=30,
            background="#ffffff",
            fieldbackground="#ffffff",
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            font=("TkDefaultFont", 10, "bold"),
            background="#e9edf1",
            foreground="#34414d",
            relief="flat",
            padding=(6, 7),
        )
        style.map(
            "Treeview",
            background=[("selected", "#dce5ee")],
            foreground=[("selected", "#1f2a35")],
        )
        style.map("Treeview.Heading", background=[("active", "#e1e6eb")])
        style.configure(
            "Deadline.TLabel",
            background="#ffffff",
            font=("TkDefaultFont", 10, "bold"),
            foreground="#65717c",
        )
        style.configure(
            "DeadlineGood.TLabel",
            background="#ffffff",
            font=("TkDefaultFont", 10, "bold"),
            foreground="#27623a",
        )
        style.configure(
            "DeadlineBad.TLabel",
            background="#ffffff",
            font=("TkDefaultFont", 10, "bold"),
            foreground="#8a3434",
        )

    def _build_layout(self) -> None:
        container = ttk.Frame(self, padding=(22, 18))
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(4, weight=1)

        ttk.Label(
            container,
            text="Оценка времени выполнения шага ПИД-регулятора",
            style="Title.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            container,
            text=(
                "Загрузите модель процессора и описание операций, "
                "затем выполните расчёт."
            ),
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(3, 16))

        files = ttk.LabelFrame(
            container, text="Входные файлы", padding=(14, 10), style="Section.TLabelframe"
        )
        files.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        files.columnconfigure(1, weight=1, minsize=190)
        files.columnconfigure(3, weight=1, minsize=200)
        ttk.Button(
            files,
            text="Выбрать модель процессора",
            command=self._select_processor,
            width=26,
        ).grid(row=0, column=0, padx=(0, 14), sticky="w")
        ttk.Label(
            files, textvariable=self.processor_path_value, style="File.TLabel"
        ).grid(
            row=0, column=1, sticky="w"
        )
        ttk.Button(
            files,
            text="Выбрать фрагмент операций",
            command=self._select_fragment,
            width=26,
        ).grid(row=0, column=2, padx=(22, 14), sticky="w")
        ttk.Label(
            files, textvariable=self.fragment_path_value, style="File.TLabel"
        ).grid(
            row=0, column=3, sticky="w"
        )

        parameters = ttk.LabelFrame(
            container,
            text="Модель процессора",
            padding=(14, 10),
            style="Section.TLabelframe",
        )
        parameters.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        labels = {
            "base_cost": "Базовая стоимость",
            "cache_miss_penalty": "Штраф промаха кэша",
            "branch_miss_penalty": "Штраф ветвления",
            "deadline": "Дедлайн",
        }
        for column, (name, label) in enumerate(labels.items()):
            parameters.columnconfigure(column, weight=1)
            block = ttk.Frame(parameters, style="Section.TFrame")
            block.grid(row=0, column=column, padx=(0, 20), sticky="ew")
            ttk.Label(block, text=label, style="Section.TLabel").grid(
                row=0, column=0, sticky="w"
            )
            ttk.Label(
                block,
                textvariable=self.parameter_values[name],
                style="Value.TLabel",
            ).grid(row=1, column=0, sticky="w", pady=(3, 0))

        operations = ttk.LabelFrame(
            container,
            text="Операции",
            padding=(10, 8),
            style="Section.TLabelframe",
        )
        operations.grid(row=4, column=0, sticky="nsew", pady=(0, 12))
        operations.columnconfigure(0, weight=1)
        operations.rowconfigure(0, weight=1)
        columns = ("name", "type", "memory", "branches", "bcet", "wcet")
        self.table = ttk.Treeview(
            operations, columns=columns, show="headings", selectmode="browse"
        )
        headings = {
            "name": "Имя операции",
            "type": "Тип",
            "memory": "Память",
            "branches": "Ветвления",
            "bcet": "BCET",
            "wcet": "WCET",
        }
        widths = {
            "name": 360,
            "type": 140,
            "memory": 85,
            "branches": 115,
            "bcet": 75,
            "wcet": 75,
        }
        for name in columns:
            self.table.heading(name, text=headings[name])
            self.table.column(
                name,
                width=widths[name],
                minwidth=70,
                anchor="center",
                stretch=name in ("name", "type"),
            )
        self.table.column("name", minwidth=250, anchor="w")
        self.table.column("type", minwidth=110, anchor="w")

        scrollbar = ttk.Scrollbar(operations, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(8, 0))

        results = ttk.LabelFrame(
            container,
            text="Результаты",
            padding=(14, 10),
            style="Section.TLabelframe",
        )
        results.grid(row=5, column=0, sticky="ew")
        result_labels = {
            "bcet": "BCET",
            "wcet": "WCET",
            "ratio": "Коэффициент",
            "memory": "Вклад памяти",
            "branches": "Вклад ветвлений",
        }
        for column, (name, label) in enumerate(result_labels.items()):
            results.columnconfigure(column, weight=1)
            block = ttk.Frame(results, style="Section.TFrame")
            block.grid(row=0, column=column, padx=(0, 18), sticky="ew")
            ttk.Label(block, text=label, style="Section.TLabel").grid(
                row=0, column=0, sticky="w"
            )
            ttk.Label(
                block, textvariable=self.result_values[name], style="Value.TLabel"
            ).grid(row=1, column=0, sticky="w", pady=(3, 0))

        self.status_label = ttk.Label(
            results, textvariable=self.status_value, style="Deadline.TLabel"
        )
        self.status_label.grid(
            row=1, column=0, columnspan=4, sticky="w", pady=(14, 0)
        )

        ttk.Button(
            results,
            text="Рассчитать",
            command=self.calculate,
            style="Accent.TButton",
        ).grid(row=1, column=4, sticky="e", pady=(12, 0))

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
            self.status_label.configure(style="DeadlineGood.TLabel")
        else:
            self.status_value.set("Дедлайн не соблюдается")
            self.status_label.configure(style="DeadlineBad.TLabel")


def main() -> None:
    WcetApp().mainloop()


if __name__ == "__main__":
    main()
