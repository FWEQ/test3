#!/usr/bin/env python3
"""Сборка отчёта по практической работе № 3 (вариант 18 «Музыкальный плеер»).

Код, таблицы спецификаций и протоколы прогонов берутся из файлов проекта,
поэтому отчёт всегда соответствует текущему состоянию репозитория.
Запуск: python report/build_report.py  →  report/Отчет_ПР3_Клочков_ФА.docx
"""

from __future__ import annotations

import re
import subprocess
import textwrap
from importlib.metadata import version
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LOGS = ROOT / "logs"
FIGURES = HERE / "figures"
TEMPLATE = HERE / "template.docx"
OUTPUT = HERE / "Отчет_ПР3_Клочков_ФА.docx"

AUTHOR = "Клочков Ф.А."
TOPIC = "Подходы для разработки программного обеспечения"

MONO = "/usr/share/fonts/liberation-mono-fonts/LiberationMono-Regular.ttf"
MONO_BOLD = "/usr/share/fonts/liberation-mono-fonts/LiberationMono-Bold.ttf"
SANS = "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf"
SANS_BOLD = "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Bold.ttf"


# ---------------------------------------------------------------------------
# Исходные данные проекта
# ---------------------------------------------------------------------------

def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def git_show(message: str, path: str) -> str:
    """Содержимое файла в коммите, сообщение которого начинается с message."""
    sha = subprocess.run(
        ["git", "log", "--format=%H", "--fixed-strings", f"--grep={message}"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()[0]
    return subprocess.run(
        ["git", "show", f"{sha}:{path}"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout


def git_history() -> list[str]:
    out = subprocess.run(
        ["git", "log", "--reverse", "--format=%s"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    return [line for line in out.splitlines() if line]


def block(src: str, header: str) -> str:
    """Определение (def/class/декорированная функция), начинающееся со строки header."""
    lines = src.splitlines()
    head = next(i for i, line in enumerate(lines) if line.strip().startswith(header))
    start = head
    while start > 0 and lines[start - 1].strip().startswith("@"):
        start -= 1
    while lines[head].strip().startswith("@"):
        head += 1
    indent = len(lines[start]) - len(lines[start].lstrip())
    end = head + 1
    while end < len(lines):
        line = lines[end]
        if line.strip() and len(line) - len(line.lstrip()) <= indent and not line.strip().startswith(")"):
            break
        end += 1
    while not lines[end - 1].strip():
        end -= 1
    return textwrap.dedent("\n".join(lines[start:end]))


def md_table(text: str, after: str | None = None) -> tuple[list[str], list[list[str]]]:
    if after:
        text = text.split(after, 1)[1]
    rows = [
        [c.strip() for c in line.strip().strip("|").split("|")]
        for line in text.splitlines()
        if line.startswith("|")
    ]
    header, _sep, *body = rows
    return header, body


def log(name: str) -> list[str]:
    return (LOGS / name).read_text(encoding="utf-8").splitlines()


# ---------------------------------------------------------------------------
# Рисунки
# ---------------------------------------------------------------------------

TERM_BG = (30, 32, 36)
TERM_FG = (215, 218, 224)
GREEN = (120, 200, 110)
RED = (235, 100, 95)
YELLOW = (225, 190, 90)
DIM = (140, 145, 155)
CYAN = (110, 185, 225)


def line_colour(line: str) -> tuple[int, int, int]:
    s = line.strip()
    if s.startswith("$"):
        return CYAN
    if re.search(r"\b(FAILED|ERROR)\b|ASSERT FAILED|Failing scenarios|Errored scenarios|^E\s", line):
        return RED
    if re.search(r"\b\d+ (failed|error)\b", line) and not re.search(r"\b0 failed, 0 skipped", line):
        if re.search(r"\b[1-9]\d* (failed|error)", line):
            return RED
    if "undefined" in line or "StepNotImplementedError" in line or "snippets" in line:
        return YELLOW
    if re.search(r"PASSED|\bpassed\b|TOTAL|100%", line):
        return GREEN
    if s.startswith(("platform", "rootdir", "configfile", "plugins", "hypothesis", "collecting", "USING")):
        return DIM
    if "#" in line and ("features/" in line):
        return TERM_FG
    return TERM_FG


def terminal(name: str, lines: list[str], title: str = "practice3-music-player — bash") -> Path:
    font = ImageFont.truetype(MONO, 17)
    bold = ImageFont.truetype(MONO_BOLD, 17)
    max_chars = 118
    lines = [ln if len(ln) <= max_chars else ln[: max_chars - 1] + "…" for ln in lines]
    char_w = font.getlength("M")
    width = int(char_w * max_chars) + 48
    line_h = 24
    height = 44 + line_h * len(lines) + 24
    img = Image.new("RGB", (width, height), TERM_BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, width, 32], fill=(48, 50, 56))
    for i, colour in enumerate([(237, 106, 94), (245, 191, 79), (98, 197, 84)]):
        d.ellipse([14 + i * 22, 10, 26 + i * 22, 22], fill=colour)
    tfont = ImageFont.truetype(SANS, 15)
    d.text((width / 2, 16), title, font=tfont, fill=(200, 200, 205), anchor="mm")
    y = 44
    for ln in lines:
        d.text((24, y), ln, font=bold if ln.startswith("$") else font, fill=line_colour(ln))
        y += line_h
    FIGURES.mkdir(exist_ok=True)
    path = FIGURES / f"{name}.png"
    img.save(path)
    return path


def pytest_excerpt(name: str, cmd: str, verbose: int | None = None, tail: int = 0, grep: str | None = None) -> list[str]:
    lines = log(name)
    out = [f"$ {cmd}"]
    out += [ln for ln in lines if ln.startswith(("platform", "rootdir", "collecting"))]
    out.append("")
    v = [ln for ln in lines if re.match(r"tests/\S+::\S.* (PASSED|FAILED|ERROR)", ln)]
    if verbose is not None and len(v) > verbose:
        out += v[:verbose] + [f"... ещё {len(v) - verbose} строк(и) ..."]
    else:
        out += v
    if grep:
        out.append("")
        found: dict[str, int] = {}
        for ln in lines:
            if re.search(grep, ln):
                found[ln] = found.get(ln, 0) + 1
        out += [f"{ln}   (×{n})" if n > 1 else ln for ln, n in found.items()]
    if tail:
        out.append("")
        out += lines[-tail:]
    return out


def arrow(d: ImageDraw.ImageDraw, pts: list[tuple[int, int]], colour=(40, 40, 40), width=3) -> None:
    d.line(pts, fill=colour, width=width, joint="curve")
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    size = 14
    left = (x2 - size * math.cos(ang - 0.4), y2 - size * math.sin(ang - 0.4))
    right = (x2 - size * math.cos(ang + 0.4), y2 - size * math.sin(ang + 0.4))
    d.polygon([(x2, y2), left, right], fill=colour)


def box(d, xy, title, subtitle="", fill=(232, 240, 250), outline=(60, 80, 110)):
    d.rounded_rectangle(xy, radius=14, fill=fill, outline=outline, width=3)
    x0, y0, x1, y1 = xy
    tf = ImageFont.truetype(SANS_BOLD, 22)
    sf = ImageFont.truetype(SANS, 18)
    cy = (y0 + y1) / 2
    if subtitle:
        d.text(((x0 + x1) / 2, cy - 14), title, font=tf, fill=(20, 20, 20), anchor="mm")
        for i, part in enumerate(subtitle.split("\n")):
            d.text(((x0 + x1) / 2, cy + 14 + i * 22), part, font=sf, fill=(60, 60, 60), anchor="mm")
    else:
        d.text(((x0 + x1) / 2, cy), title, font=tf, fill=(20, 20, 20), anchor="mm")


def architecture_figure() -> Path:
    w, h = 1500, 760
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    test_fill, code_fill, spec_fill = (226, 239, 218), (222, 233, 247), (252, 239, 214)
    box(d, (30, 260, 330, 370), "tests/unit", "TDD · pytest", test_fill)
    box(d, (390, 40, 720, 150), "tests/acceptance", "ATDD · pytest + TestClient", test_fill)
    box(d, (780, 40, 1110, 150), "features", "BDD · behave (Gherkin)", test_fill)
    box(d, (1170, 40, 1470, 150), "tests/spec", "SDD · pytest", test_fill)
    box(d, (1170, 230, 1470, 340), "specs/", "playback_examples.md", spec_fill)
    box(d, (390, 260, 720, 370), "player/api.py", "REST API · FastAPI", code_fill)
    box(d, (300, 520, 1200, 660), "player/core.py",
        "Track · Player · PlayerState\nисключения предметной области", code_fill)
    box(d, (30, 40, 330, 150), "acceptance/", "criteria.md (АК-1…АК-8)", spec_fill)

    arrow(d, [(180, 370), (180, 470), (420, 470), (420, 520)])
    arrow(d, [(555, 150), (555, 260)])
    arrow(d, [(555, 370), (555, 520)])
    arrow(d, [(945, 150), (945, 520)])
    arrow(d, [(1210, 150), (1210, 190), (1140, 190), (1140, 470), (1080, 470), (1080, 520)])
    arrow(d, [(1400, 230), (1400, 150)], colour=(150, 110, 40))
    arrow(d, [(330, 95), (390, 95)], colour=(150, 110, 40))

    lf = ImageFont.truetype(SANS, 18)
    d.text((1390, 190), "читает таблицу", font=lf, fill=(150, 110, 40), anchor="rm")
    d.line([(40, 715), (80, 715)], fill=(40, 40, 40), width=3)
    d.text((90, 715), "вызывает / тестирует", font=lf, fill=(40, 40, 40), anchor="lm")
    d.line([(330, 715), (370, 715)], fill=(150, 110, 40), width=3)
    d.text((380, 715), "источник требований для тестов", font=lf, fill=(150, 110, 40), anchor="lm")
    path = FIGURES / "arch.png"
    img.save(path)
    return path


def state_figure() -> Path:
    w, h = 1500, 560
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    lf = ImageFont.truetype(SANS, 19)
    states = {"STOPPED": (90, 200, 390, 300), "PLAYING": (600, 200, 900, 300), "PAUSED": (1110, 200, 1410, 300)}
    names = {"STOPPED": "остановлен", "PLAYING": "воспроизведение", "PAUSED": "пауза"}
    for key, xy in states.items():
        box(d, xy, key, names[key])
    d.ellipse([20, 235, 50, 265], fill=(30, 30, 30))
    arrow(d, [(50, 250), (90, 250)])

    def label(x, y, text):
        d.text((x, y), text, font=lf, fill=(30, 30, 30), anchor="mm")

    arrow(d, [(390, 225), (600, 225)]); label(495, 205, "play")
    arrow(d, [(600, 275), (390, 275)]); label(495, 300, "stop, конец плейлиста")
    arrow(d, [(900, 225), (1110, 225)]); label(1005, 205, "pause")
    arrow(d, [(1110, 275), (900, 275)]); label(1005, 300, "play")
    arrow(d, [(1260, 300), (1260, 420), (240, 420), (240, 300)])
    label(750, 445, "stop, next, previous (смена трека из паузы)")
    arrow(d, [(700, 200), (700, 120), (800, 120), (800, 200)])
    label(750, 95, "next, previous, tick — трек меняется, воспроизведение продолжается")
    label(750, 510, "pause в состоянии «остановлен» — ошибка PlayerStateError (HTTP 409)")
    path = FIGURES / "states.png"
    img.save(path)
    return path


# ---------------------------------------------------------------------------
# Вёрстка
# ---------------------------------------------------------------------------

class Report:
    def __init__(self) -> None:
        self.doc = Document(TEMPLATE)
        self.table_no = 0
        self.figure_no = 0
        self.listing_no = 0
        self.grid = next(s for s in self.doc.styles if s.style_id == "ad")

    # --- абзацы ------------------------------------------------------------
    def p(self, text: str = "", *, indent: bool = True, align: str = "justify", bold: bool = False,
          before: float | None = None, after: float | None = None, keep_next: bool = False):
        par = self.doc.add_paragraph()
        par.alignment = {
            "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
            "center": WD_ALIGN_PARAGRAPH.CENTER,
            "left": WD_ALIGN_PARAGRAPH.LEFT,
        }[align]
        pf = par.paragraph_format
        pf.first_line_indent = Cm(1.25) if indent else Cm(0)
        if before is not None:
            pf.space_before = Pt(before)
        if after is not None:
            pf.space_after = Pt(after)
        if keep_next:
            pf.keep_with_next = True
        if text:
            par.add_run(text).bold = bold
        return par

    def items(self, lines: list[str], numbered: bool = True) -> None:
        for i, line in enumerate(lines, 1):
            last = i == len(lines)
            mark = f"{i})" if numbered else "–"
            end = "." if last else ";"
            self.p(f"{mark} {line}{end}")

    def h1(self, text: str, new_page: bool = False) -> None:
        par = self.p(text, indent=False, align="center", bold=True, before=12, after=8, keep_next=True)
        if new_page:
            par.paragraph_format.page_break_before = True

    def h2(self, text: str) -> None:
        self.p(text, indent=False, bold=True, before=6, after=4, keep_next=True)

    def h3(self, text: str) -> None:
        par = self.p(keep_next=True)
        par.add_run(text).italic = True

    def page_break(self) -> None:
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # --- таблицы -----------------------------------------------------------
    def caption(self, text: str) -> None:
        self.p(text, indent=False, align="center", before=10, after=4, keep_next=True)

    def table(self, title: str, header: list[str], rows: list[list[str]], widths: list[float],
              center: tuple[int, ...] = (0,), size: float = 12) -> None:
        self.table_no += 1
        self.caption(f"Таблица {self.table_no} – {title}")
        t = self.doc.add_table(rows=1 + len(rows), cols=len(header))
        t.style = self.grid
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        for col, w in zip(t.columns, widths):
            col.width = Cm(w)
        for r, values in enumerate([header] + rows):
            row = t.rows[r]
            tr_pr = row._tr.get_or_add_trPr()
            cant = OxmlElement("w:cantSplit")
            tr_pr.append(cant)
            if r == 0:
                hdr = OxmlElement("w:tblHeader")
                tr_pr.append(hdr)
            for c, value in enumerate(values):
                cell = row.cells[c]
                cell.width = Cm(widths[c])
                par = cell.paragraphs[0]
                pf = par.paragraph_format
                pf.first_line_indent = Cm(0)
                pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
                pf.space_after = Pt(0)
                par.alignment = WD_ALIGN_PARAGRAPH.CENTER if (r == 0 or c in center) else WD_ALIGN_PARAGRAPH.LEFT
                run = par.add_run(value)
                run.font.size = Pt(size)
                run.bold = r == 0
                if r == 0:
                    shd = OxmlElement("w:shd")
                    shd.set(qn("w:val"), "clear")
                    shd.set(qn("w:color"), "auto")
                    shd.set(qn("w:fill"), "D9E2F3")
                    cell._tc.get_or_add_tcPr().append(shd)
        self.p(after=0)

    # --- рисунки и листинги -----------------------------------------------
    def figure(self, path: Path, title: str, width_cm: float = 16.5) -> None:
        self.figure_no += 1
        par = self.p(indent=False, align="center", before=6, keep_next=True)
        par.add_run().add_picture(str(path), width=Cm(width_cm))
        self.p(f"Рисунок {self.figure_no} – {title}", indent=False, align="center", after=8)

    def listing(self, title: str, code: str, label: str | None = None, numbers: bool = True) -> None:
        if label is None:
            self.listing_no += 1
            label = str(self.listing_no)
        self.caption(f"Листинг {label} – {title}")
        lines = code.rstrip("\n").splitlines()
        for i, line in enumerate(lines, 1):
            par = self.doc.add_paragraph()
            pf = par.paragraph_format
            pf.first_line_indent = Cm(0)
            pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
            pf.space_after = Pt(0)
            if i < len(lines):
                pf.keep_with_next = len(lines) <= 30
            text = f"{i:03d}  {line}" if numbers else line
            run = par.add_run(text)
            run.font.name = "Courier New"
            run._element.rPr.rFonts.set(qn("w:eastAsia"), "Courier New")
            run.font.size = Pt(10)
        self.p(after=0)

    # --- титульный лист -----------------------------------------------------
    def title_page(self) -> None:
        paras = self.doc.paragraphs
        title = next(p for p in paras if p.text.startswith("Отчет по практической работе"))
        title.runs[0].text = "Отчет по практической работе №3"
        for r in title.runs[1:]:
            r.text = ""
        topic = next(p for p in paras if p.text.startswith("Тема практической работы"))
        runs = topic.runs
        quote = next(i for i, r in enumerate(runs) if r.text == "«")
        runs[quote + 1].text = TOPIC
        for r in runs[quote + 2:]:
            r.text = ""
        runs[-1].text = "»" if runs[-1] is not runs[quote + 1] else runs[-1].text
        cp = self.doc.core_properties
        cp.author = AUTHOR
        cp.last_modified_by = AUTHOR
        cp.title = f"Отчёт по практической работе №3. {TOPIC}"
        cp.subject = "Тестирование и верификация ПО"
        cp.comments = ""

    def save(self) -> None:
        self.doc.save(OUTPUT)


# ---------------------------------------------------------------------------
# Содержание отчёта
# ---------------------------------------------------------------------------

def build() -> None:
    core = read("player/core.py")
    api = read("player/api.py")
    unit = read("tests/unit/test_player.py")
    acceptance = read("tests/acceptance/test_player_api.py")
    spec_test = read("tests/spec/test_playback_spec.py")
    feature = read("features/playback.feature")
    feature_empty = read("features/empty_playlist.feature")
    steps = read("features/steps/player_steps.py")
    environment = read("features/environment.py")
    criteria_header, criteria = md_table(read("acceptance/criteria.md"))
    spec_md = read("specs/playback_examples.md")
    spec_header, spec_rows = md_table(spec_md, after="## Примеры")
    core_green = git_show("TDD (green)", "player/core.py")
    core_refactor = git_show("TDD (refactor)", "player/core.py")
    history = git_history()

    FIGURES.mkdir(exist_ok=True)
    figs = {
        "arch": architecture_figure(),
        "states": state_figure(),
        "tdd_red": terminal("01_tdd_red", pytest_excerpt(
            "01_tdd_red.txt", "python -m pytest tests/unit -v", verbose=12, tail=1)),
        "tdd_green": terminal("02_tdd_green", pytest_excerpt(
            "02_tdd_green.txt", "python -m pytest tests/unit -v", tail=1)),
        "tdd_refactor": terminal("03_tdd_refactor", pytest_excerpt(
            "03_tdd_refactor.txt", "python -m pytest tests/unit -v --cov=player --cov-report=term-missing",
            verbose=6, tail=10)),
        "atdd_red": terminal("04_atdd_red", pytest_excerpt(
            "04_atdd_red.txt", "python -m pytest tests/acceptance -v",
            grep=r"^E\s+(assert 404|AssertionError: assert 404|\+  where 404)", tail=10)),
        "atdd_green": terminal("05_atdd_green", pytest_excerpt(
            "05_atdd_green.txt", "python -m pytest tests/acceptance -v", tail=1)),
        "bdd_undefined": terminal("06_bdd_undefined", ["$ python -m behave"] + log("06_bdd_red_undefined.txt")[-34:]),
        "bdd_red": terminal("07_bdd_red", ["$ python -m behave"] + bdd_failure_excerpt()),
        "bdd_green": terminal("08_bdd_green", ["$ python -m behave"] + log("08_bdd_green.txt")[:10]
                              + ["..."] + log("08_bdd_green.txt")[-5:]),
        "sdd_red": terminal("09_sdd_red", pytest_excerpt(
            "09_sdd_red.txt", "python -m pytest tests/spec -v",
            grep=r"^E\s+AttributeError", tail=1)),
        "sdd_green": terminal("10_sdd_green", pytest_excerpt(
            "10_sdd_green.txt", "python -m pytest tests/spec -v", tail=1)),
        "final": terminal("11_final", final_excerpt()),
    }

    r = Report()
    r.title_page()

    # --- Содержание ---------------------------------------------------------
    toc = [
        "1 Цель и задачи работы",
        "2 Теоретические основы",
        "2.1 Test-Driven Development (TDD)",
        "2.2 Acceptance Test-Driven Development (ATDD)",
        "2.3 Behavior-Driven Development (BDD)",
        "2.4 Specification by Example (SDD)",
        "3 Практическая часть",
        "3.1 Вариант задания и условия разработки",
        "3.2 Архитектура программного продукта",
        "3.3 Разработка с использованием TDD",
        "3.4 Разработка с использованием ATDD",
        "3.5 Разработка с использованием BDD",
        "3.6 Разработка с использованием SDD",
        "3.7 Итоговое тестирование",
        "4 Анализ подходов",
        "Заключение",
        "Список использованных источников",
        "Приложение А. Исходный код программного продукта",
        "Приложение Б. Модульные, приёмочные и спецификационные тесты",
        "Приложение В. Сценарии BDD и определения шагов",
        "Приложение Г. Протокол итогового прогона тестов",
    ]
    r.p("Содержание", indent=False, align="center", bold=True, before=12, after=8)
    for line in toc:
        r.p(line, indent=False)

    # --- 1 ------------------------------------------------------------------
    r.h1("1 Цель и задачи работы", new_page=True)
    r.p("Цель работы – изучить и применить подходы к разработке программного обеспечения, основанные "
        "на тестировании (TDD, ATDD, BDD и SDD), для повышения качества, надёжности и поддерживаемости кода.")
    r.p("В ходе работы выполнены следующие задачи:")
    r.items([
        "изучены теоретические основы методологий TDD, ATDD, BDD и SDD (Specification by Example)",
        "исследованы преимущества и недостатки каждого подхода",
        "по варианту 18 разработан программный продукт «Музыкальный плеер», причём каждая часть его "
        "функциональности создана с применением одного из четырёх подходов",
        "проанализировано влияние интеграции тестирования на архитектуру и качество продукта",
        "подготовлен отчёт с выводами и рекомендациями по интеграции подходов в процесс разработки",
    ])

    # --- 2 ------------------------------------------------------------------
    r.h1("2 Теоретические основы")
    r.h2("2.1 Test-Driven Development (TDD)")
    r.p("TDD (разработка через тестирование) – методология, при которой тест на новую функциональность "
        "пишется до её реализации. Разработка ведётся короткими циклами «красный – зелёный – рефакторинг»: "
        "сначала создаётся тест, описывающий ожидаемое поведение, и запускается – он падает, поскольку кода "
        "ещё нет; затем пишется минимальный код, достаточный для прохождения теста; после этого код "
        "улучшается без изменения поведения, а тесты подтверждают, что ничего не сломано.")
    r.p("Основной инструмент TDD – модульные (unit) тесты, проверяющие отдельные функции и классы в изоляции. "
        "Подход ориентирован на разработчика: он задаёт техническую спецификацию кода и даёт быструю обратную связь.")
    r.h2("2.2 Acceptance Test-Driven Development (ATDD)")
    r.p("ATDD (разработка через приёмочные тесты) начинается с совместного обсуждения требований заказчиком, "
        "аналитиком, тестировщиком и разработчиком. Результатом обсуждения становятся приёмочные критерии – "
        "сценарии вида «предусловие – действия – ожидаемый результат», которые автоматизируются до начала "
        "реализации. Функциональность считается готовой, когда проходят все приёмочные тесты.")
    r.p("В отличие от TDD, приёмочные тесты проверяют систему «снаружи» – через пользовательский или "
        "программный интерфейс, – и отвечают на вопрос «делает ли система то, что нужно заказчику».")
    r.h2("2.3 Behavior-Driven Development (BDD)")
    r.p("BDD (разработка через поведение) развивает идеи TDD: поведение системы описывается на естественном "
        "языке в виде сценариев со структурой Given – When – Then (Дано – Когда – Тогда). Сценарии записываются "
        "на языке Gherkin и одновременно служат документацией и автоматизированными тестами: каждому шагу "
        "сценария сопоставляется функция-определение шага (step definition) в коде.")
    r.p("Для автоматизации используются Cucumber (Java, JavaScript), SpecFlow (.NET) и behave (Python). "
        "Gherkin поддерживает русские ключевые слова (Функция, Сценарий, Дано, Когда, Тогда), что делает "
        "сценарии понятными участникам проекта, не владеющим программированием.")
    r.h2("2.4 Specification by Example (SDD)")
    r.p("Specification by Example (в методических указаниях – SDD) – подход, при котором требования "
        "описываются не абстрактными формулировками, а конкретными примерами: таблицами входных данных и "
        "ожидаемых результатов. Примеры собираются вместе с заказчиком, устраняют двусмысленность "
        "требований и напрямую преобразуются в автоматизированные тесты.")
    r.p("Ключевое свойство подхода – «живая документация»: если тесты читают примеры непосредственно из "
        "спецификации, то спецификация не может разойтись с поведением системы.")

    # --- 3 ------------------------------------------------------------------
    r.h1("3 Практическая часть")
    r.h2("3.1 Вариант задания и условия разработки")
    r.p("Номер студенческого билета – 24И0418, последние две цифры – 18, что соответствует варианту 18 "
        "«Музыкальный плеер». Функции по заданию: воспроизведение, пауза, переключение треков. Для "
        "подходов заданы: TDD – тесты корректного переключения треков и управления воспроизведением; "
        "ATDD – сценарии воспроизведения для проверки пользовательского опыта; BDD – сценарий «Given треки "
        "загружены, When нажимаю «play», Then начинается воспроизведение»; SDD – спецификации с входными "
        "данными (список треков) и ожидаемыми состояниями плеера.")
    r.p("Чтобы каждый подход действительно управлял разработкой, а не проверял уже готовый код, "
        "функциональность разделена между этапами: каждый этап начинается с тестов на ещё не "
        "реализованное поведение (таблица 2). Условия разработки приведены в таблице 1.")
    r.table("Условия разработки", ["Параметр", "Значение"], [
        ["Язык программирования", f"Python {sys_python()}"],
        ["Модульные, приёмочные и спецификационные тесты", f"pytest {version('pytest')}, pytest-cov {version('pytest-cov')}"],
        ["Программный интерфейс (ATDD)", f"FastAPI {version('fastapi')}, тестовый клиент на httpx {version('httpx')}"],
        ["Сценарии поведения (BDD)", f"behave {version('behave')}, язык Gherkin (русские ключевые слова)"],
        ["Сервер для ручной проверки API", f"uvicorn {version('uvicorn')}"],
        ["Контроль версий", "git: каждый этап «красный / зелёный / рефакторинг» – отдельный коммит"],
        ["Операционная система", "Fedora Linux 43"],
    ], [7.5, 9.0])
    r.table("Функциональность плеера и подход, которым она разработана", ["Функция", "Описание", "Подход"], [
        ["Трек", "название, исполнитель, длительность; пустое название и неположительная длительность запрещены", "TDD"],
        ["Загрузка плейлиста", "первый трек становится текущим, плеер остановлен", "TDD"],
        ["play / pause / stop", "запуск, приостановка и продолжение, остановка; пауза без воспроизведения – ошибка", "TDD"],
        ["next / previous", "переключение треков; на последнем треке next останавливает плеер", "TDD"],
        ["REST API", "управление плеером по HTTP, коды ответов 200 / 400 / 409", "ATDD"],
        ["Режим повтора", "после последнего трека – первый, перед первым – последний", "BDD"],
        ["Ход времени (tick)", "позиция в треке, автопереход к следующему треку с переносом остатка", "SDD"],
        ["Правило «назад»", "если трек играет более 3 с, previous перезапускает его", "SDD"],
    ], [3.8, 10.2, 2.5])

    r.h2("3.2 Архитектура программного продукта")
    r.p("Продукт разделён на доменный слой и слой интерфейса. Доменная логика (модуль player/core.py) не "
        "зависит от фреймворков и содержит классы Track (неизменяемый трек), Player (состояние плеера, "
        "плейлист, позиция) и перечисление PlayerState. REST API (player/api.py) – тонкая обёртка, которая "
        "преобразует HTTP-запросы в вызовы методов Player, а исключения предметной области – в коды ответов. "
        "Связь модулей с тестовыми наборами показана на рисунке 1, состояния плеера – на рисунке 2.")
    r.figure(figs["arch"], "Структура проекта и связь кода с тестами", 16.5)
    r.figure(figs["states"], "Диаграмма состояний плеера", 16.5)
    r.table("Состав проекта", ["Путь", "Назначение"], [
        ["player/core.py", "доменная логика плеера"],
        ["player/api.py", "REST API на FastAPI"],
        ["tests/unit/test_player.py", "модульные тесты (TDD)"],
        ["acceptance/criteria.md", "приёмочные критерии АК-1 – АК-8 (ATDD)"],
        ["tests/acceptance/test_player_api.py", "автоматизированные приёмочные тесты (ATDD)"],
        ["features/*.feature", "сценарии на языке Gherkin (BDD)"],
        ["features/steps/player_steps.py", "определения шагов behave (BDD)"],
        ["specs/playback_examples.md", "спецификация на примерах (SDD)"],
        ["tests/spec/test_playback_spec.py", "тесты, генерируемые из таблицы спецификации (SDD)"],
        ["logs/", "протоколы прогонов каждого этапа"],
    ], [7.5, 9.0], center=())

    # --- 3.3 TDD ------------------------------------------------------------
    r.h2("3.3 Разработка с использованием TDD")
    r.p("С помощью TDD разработано ядро плеера: трек, загрузка плейлиста, воспроизведение, пауза, остановка "
        "и переключение треков.")
    r.h3("Шаг 1. Создание тестов")
    r.p("До написания кода составлены 25 модульных тестов (с учётом параметризации), описывающих "
        "ожидаемое поведение. Тесты сгруппированы по функциям (таблица 4); общие тестовые данные вынесены "
        "в фикстуры pytest. Фрагмент тестов приведён в листинге 1, полный текст – в приложении Б.")
    r.table("Модульные тесты ядра плеера", ["Группа", "Тесты", "Что проверяется"], [
        ["Трек", "3 (5 с параметрами)", "сохранение метаданных, запрет пустого названия и неположительной длительности"],
        ["Загрузка", "4", "новый плеер пуст и остановлен; первый трек текущий; повторная загрузка сбрасывает состояние; плейлист копируется"],
        ["play / pause / stop", "6 (7)", "запуск, ошибка при пустом плейлисте, повторный play, пауза, ошибка паузы вне воспроизведения, продолжение после паузы, остановка"],
        ["next / previous", "7 (8)", "переход вперёд и назад, сохранение воспроизведения, остановка при смене трека на паузе и в конце плейлиста, ошибки при пустом плейлисте"],
    ], [3.3, 3.0, 10.2])
    r.listing("Фрагмент модульных тестов переключения треков",
              "\n\n".join([block(unit, "def player("), block(unit, "def test_next_keeps_playing"),
                           block(unit, "def test_next_on_last_track_stops_playback")]))
    r.h3("Шаг 2. Запуск тестов")
    r.p("Для того чтобы тесты собирались, создан модуль-заглушка с объявлениями классов и исключений, "
        "конструкторы которых выбрасывают NotImplementedError. Все 25 тестов не проходят: 9 падают в теле "
        "теста, 16 – при подготовке фикстуры (рисунок 3). Это ожидаемый «красный» этап.")
    r.figure(figs["tdd_red"], "Красный этап TDD: тесты падают, реализация отсутствует")
    r.h3("Шаг 3. Реализация функциональности")
    r.p("Написан минимальный код, достаточный для прохождения тестов. На этом этапе допускались "
        "дублирование (проверка пустого плейлиста повторена в трёх методах) и открытые для записи атрибуты. "
        "Методы переключения треков в первой версии приведены в листинге 2.")
    r.listing("Минимальная реализация переключения треков (этап «зелёный»)",
              "\n\n".join([block(core_green, "def next("), block(core_green, "def previous(")]))
    r.h3("Шаг 4. Повторный запуск тестов")
    r.p("Все 25 тестов пройдены (рисунок 4).")
    r.figure(figs["tdd_green"], "Зелёный этап TDD: все модульные тесты пройдены")
    r.h3("Шаг 5. Рефакторинг")
    r.p("После прохождения тестов выполнен рефакторинг без изменения поведения:")
    r.items([
        "Track преобразован в неизменяемый dataclass с проверкой данных в __post_init__",
        "состояние плеера закрыто от внешней записи: доступ только через свойства playlist, state, index, current_track",
        "повторяющаяся проверка пустого плейлиста вынесена в метод _require_playlist",
        "правило «смена трека сохраняет воспроизведение, иначе плеер останавливается» вынесено в метод _switch_to",
        "добавлены аннотации типов и документирующие строки исключений",
    ], numbered=True)
    r.listing("Переключение треков после рефакторинга",
              "\n\n".join([block(core_refactor, "def next("), block(core_refactor, "def previous("),
                           block(core_refactor, "def _require_playlist("), block(core_refactor, "def _switch_to(")]))
    r.p("Повторный прогон подтвердил, что поведение не изменилось; покрытие операторов модуля модульными "
        "тестами составило 98 % (рисунок 5). Непокрытым осталось только свойство index, которое "
        "используется на следующем этапе в REST API.")
    r.figure(figs["tdd_refactor"], "Прогон после рефакторинга с измерением покрытия")

    # --- 3.4 ATDD -----------------------------------------------------------
    r.h2("3.4 Разработка с использованием ATDD")
    r.p("С помощью ATDD разработан программный интерфейс плеера (REST API), через который с плеером "
        "работает пользовательское приложение.")
    r.h3("Шаг 1. Согласование приёмочных критериев")
    r.p("Работа индивидуальная, поэтому роли заказчика (владельца продукта), тестировщика и разработчика "
        "выполнял автор. Требования сформулированы с точки зрения пользователя и зафиксированы в файле "
        "acceptance/criteria.md до начала реализации (таблица 5). Тестовый плейлист: «Intro» (180 с), "
        "«Song» (200 с), «Outro» (150 с).")
    r.table("Приёмочные критерии REST API плеера", criteria_header, criteria, [1.3, 3.0, 3.6, 3.6, 5.0], center=(0,))
    r.h3("Шаг 2. Автоматизация приёмочных тестов")
    r.p("Каждый критерий преобразован в тест, который обращается к приложению через HTTP с помощью "
        "тестового клиента FastAPI (TestClient), не запуская сервер. Тесты проверяют коды ответов и "
        "содержимое JSON, то есть поведение, наблюдаемое пользователем (листинг 4).")
    r.listing("Приёмочные тесты АК-5 и АК-6",
              "\n\n".join([block(acceptance, "def press("), block(acceptance, "def test_ac5_end_of_playlist_stops"),
                           block(acceptance, "def test_ac6_play_with_empty_playlist")]))
    r.h3("Шаг 3. Запуск тестов")
    r.p("Создано пустое приложение FastAPI без маршрутов. Все 8 приёмочных тестов не проходят: на любой "
        "запрос сервер отвечает 404 (рисунок 6).")
    r.figure(figs["atdd_red"], "Красный этап ATDD: маршруты API отсутствуют")
    r.h3("Шаг 4. Реализация функциональности")
    r.p("Реализован REST API (таблица 6). Исключения предметной области централизованно преобразуются "
        "в коды ответов: пустой плейлист и некорректный трек – 400, недопустимая операция в текущем "
        "состоянии – 409. Новый плейлист сначала полностью проверяется и только затем загружается, поэтому "
        "некорректный запрос не портит прежний плейлист (критерий АК-8). Фрагмент кода – в листинге 5.")
    r.table("Методы REST API", ["Метод и путь", "Назначение", "Ответы"], [
        ["GET /player", "текущее состояние: режим, трек, позиция, плейлист", "200"],
        ["PUT /playlist", "загрузка плейлиста", "200, 400"],
        ["POST /player/play", "запуск или продолжение воспроизведения", "200, 400"],
        ["POST /player/pause", "приостановка", "200, 409"],
        ["POST /player/stop", "остановка", "200"],
        ["POST /player/next", "следующий трек", "200, 400"],
        ["POST /player/previous", "предыдущий трек", "200, 400"],
    ], [5.0, 8.5, 3.0], center=(2,))
    r.listing("Фабрика приложения REST API", block(api, "def create_app("))
    r.h3("Шаг 5. Повторный запуск тестов")
    r.p("Все 8 приёмочных тестов пройдены (рисунок 7), модульные тесты при этом также остались зелёными. "
        "Рефакторинг не потребовался: обработчики ошибок и действий с самого начала вынесены в "
        "функции-фабрики. Работа API дополнительно проверена вручную через uvicorn и curl.")
    r.figure(figs["atdd_green"], "Зелёный этап ATDD: все приёмочные критерии выполнены")

    # --- 3.5 BDD ------------------------------------------------------------
    r.h2("3.5 Разработка с использованием BDD")
    r.p("С помощью BDD описано поведение плеера с точки зрения слушателя и разработана новая функция – "
        "режим повтора плейлиста.")
    r.h3("Шаг 1. Написание сценариев")
    r.p("Сценарии записаны на языке Gherkin с русскими ключевыми словами (директива # language: ru). "
        "Предыстория загружает тестовый плейлист в виде таблицы; сценарий «Запуск воспроизведения кнопкой "
        "«play»» дословно реализует сценарий варианта «Given треки загружены, When нажимаю «play», Then "
        "начинается воспроизведение». Режим повтора описан структурами сценария (Scenario Outline) с "
        "таблицами примеров: одни и те же шаги выполняются при выключенном и включённом повторе. Всего "
        "8 сценариев в двух файлах; фрагмент – в листинге 6, полный текст – в приложении В.")
    feature_lines = feature.splitlines()
    r.listing("Фрагмент файла features/playback.feature",
              "\n".join(feature_lines[:17] + ["  ..."] + feature_lines[34:45]))
    r.h3("Шаг 2. Автоматизация сценариев")
    r.p("При первом запуске behave сообщил, что все 46 шагов не определены, и предложил заготовки "
        "функций (рисунок 8).")
    r.figure(figs["bdd_undefined"], "Первый запуск behave: шаги не определены")
    r.p("Затем написаны определения шагов (листинг 7). Шаги параметризованы: например, шаблон "
        "«я нажимаю \"{button}\"» обрабатывает все кнопки плеера, а словари переводят русские названия "
        "состояний и режимов в значения перечислений. Перед каждым сценарием в environment.py создаётся "
        "новый экземпляр плеера, поэтому сценарии не зависят друг от друга.")
    r.listing("Фрагмент определений шагов",
              "\n\n".join([block(steps, '@given("треки загружены'), block(steps, '@given("режим повтора'),
                           block(steps, '@step(\'я нажимаю'), block(steps, '@then(\'текущий трек')]))
    r.p("Повторный запуск: 6 сценариев проходят на уже существующей логике, 2 сценария режима повтора "
        "падают – после последнего трека плеер останавливается вместо перехода к первому (рисунок 9).")
    r.figure(figs["bdd_red"], "Красный этап BDD: сценарии режима повтора не выполняются")
    r.h3("Шаг 3. Реализация поведения")
    r.p("В класс Player добавлен атрибут repeat, а методы next и previous дополнены ветвями для "
        "режима повтора (листинг 8).")
    core_bdd = git_show("BDD (green)", "player/core.py")
    r.listing("Переключение треков с учётом режима повтора",
              "\n\n".join([block(core_bdd, "def next("), block(core_bdd, "def previous(")]))
    r.h3("Шаг 4. Повторный запуск сценариев")
    r.p("Все 8 сценариев (46 шагов) выполнены успешно (рисунок 10), модульные и приёмочные тесты "
        "остались зелёными.")
    r.figure(figs["bdd_green"], "Зелёный этап BDD: все сценарии выполнены")
    r.h3("Шаг 5. Рефакторинг")
    r.p("Изменение затронуло два метода и не создало дублирования, поэтому отдельный рефакторинг не "
        "потребовался; сценарии остаются исполняемой документацией поведения плеера.")

    # --- 3.6 SDD ------------------------------------------------------------
    r.h2("3.6 Разработка с использованием SDD")
    r.p("С помощью Specification by Example разработаны ход времени воспроизведения, автоматический "
        "переход к следующему треку и правило кнопки «назад» – поведение, которое удобнее всего задать "
        "набором конкретных примеров.")
    r.h3("Шаг 1. Документирование примеров")
    r.p("Примеры собраны в файле specs/playback_examples.md. Сначала сформулированы правила:")
    rules = re.findall(r"^\d\. (.+?)(?=\n\d\.|\n\n)", spec_md.split("## Правила", 1)[1], flags=re.S | re.M)
    r.items([re.sub(r"\s+", " ", rule).rstrip(".") for rule in rules])
    r.p("Затем для стандартного плейлиста «Intro» (180 с), «Song» (200 с), «Outro» (150 с) и пустого "
        "плейлиста составлены 17 примеров: обычные случаи, граничные значения (ровно длительность трека, "
        "ровно 3 с для правила «назад», конец плейлиста) и ошибочные действия (таблица 7). Действия "
        "перечисляются через точку с запятой, «tick N» означает, что прошло N секунд.")
    r.table("Спецификация на примерах: состояние плеера после действий", spec_header, spec_rows,
            [0.7, 2.6, 1.3, 3.6, 1.3, 2.0, 1.5, 3.5], center=(0, 2, 4, 5, 6), size=10.5)
    r.h3("Шаг 2. Создание спецификаций и автоматизированных тестов")
    r.p("Тест не дублирует данные таблицы, а читает её прямо из файла спецификации: функция "
        "read_examples разбирает Markdown-таблицу, а декоратор pytest.mark.parametrize превращает каждую "
        "строку в отдельный тест (листинг 9). Добавление строки в спецификацию автоматически добавляет "
        "тест – спецификация становится «живой документацией».")
    r.listing("Генерация тестов из таблицы спецификации",
              "\n\n".join([block(spec_test, "def read_examples("), block(spec_test, "def apply("),
                           block(spec_test, "def test_playback_example(")]))
    r.h3("Шаг 3. Запуск тестов")
    r.p("Все 17 примеров не проходят: у плеера ещё нет метода tick и свойства position (рисунок 11).")
    r.figure(figs["sdd_red"], "Красный этап SDD: функциональность времени отсутствует")
    r.h3("Шаг 4. Реализация функциональности")
    r.p("В Player добавлены позиция воспроизведения, метод tick и порог перезапуска трека "
        "RESTART_THRESHOLD = 3 с. Метод tick в цикле переносит «лишние» секунды на следующие треки, "
        "поэтому один вызов может пройти несколько треков (примеры 8 и 9). Переключение трека и остановка "
        "сбрасывают позицию, пауза сохраняет её (листинг 10). Позиция и режим повтора добавлены также в "
        "ответ REST API.")
    r.listing("Ход времени и правило кнопки «назад»",
              "\n\n".join([block(core, "def tick("), block(core, "def previous(")]))
    r.h3("Шаг 5. Повторный запуск тестов")
    r.p("Все 17 примеров спецификации выполнены (рисунок 12). Регрессий в тестах предыдущих этапов нет.")
    r.figure(figs["sdd_green"], "Зелёный этап SDD: все примеры спецификации выполнены")

    # --- 3.7 ----------------------------------------------------------------
    r.h2("3.7 Итоговое тестирование")
    r.p("После завершения всех этапов выполнен общий прогон тестов (рисунок 13, полный протокол – в "
        "приложении Г). Сводные результаты приведены в таблице 8. Покрытие операторов кода тестами pytest "
        "составило 99 %; две непокрытые строки – возврат None для пустого трека в API и ветвь previous в "
        "режиме повтора, которая покрыта сценариями behave.")
    r.figure(figs["final"], "Итоговый прогон всех тестов")
    r.table("Результаты итогового тестирования", ["Подход", "Набор тестов", "Количество", "Результат"], [
        ["TDD", "tests/unit", "25 тестов", "все пройдены"],
        ["ATDD", "tests/acceptance", "8 тестов", "все пройдены"],
        ["BDD", "features", "8 сценариев, 46 шагов", "все выполнены"],
        ["SDD", "tests/spec", "17 примеров", "все пройдены"],
        ["Итого", "", "58 проверок", "покрытие 99 %"],
    ], [2.5, 4.5, 4.5, 5.0], center=(0, 2, 3))
    r.p("История разработки сохранена в git: каждый «красный», «зелёный» этап и рефакторинг оформлены "
        "отдельным коммитом, что подтверждает порядок работы «тест – код» (таблица 9). Протоколы каждого "
        "прогона сохранены в каталоге logs.")
    r.table("История коммитов", ["№", "Сообщение коммита"], [[str(i), msg] for i, msg in enumerate(history, 1)],
            [1.2, 15.3])

    # --- 4 ------------------------------------------------------------------
    r.h1("4 Анализ подходов")
    r.p("Все четыре подхода интегрируют тестирование в разработку, но различаются тем, кто формулирует "
        "проверки, на каком уровне они работают и кому адресован результат (таблица 10).")
    r.table("Сравнение подходов", ["Критерий", "TDD", "ATDD", "BDD", "SDD"], [
        ["Основа", "модульные тесты", "приёмочные критерии", "сценарии поведения", "таблицы примеров"],
        ["Кто формулирует", "разработчик", "заказчик, аналитик, тестировщик, разработчик", "команда и бизнес", "заказчик и команда"],
        ["Уровень проверки", "класс, функция", "система через интерфейс", "поведение системы", "бизнес-правило"],
        ["Язык описания", "код", "текст критериев и код", "Gherkin (естественный язык)", "таблицы"],
        ["Инструменты в работе", "pytest", "pytest, FastAPI TestClient", "behave", "pytest (parametrize)"],
        ["Что разработано", "ядро плеера", "REST API", "режим повтора", "ход времени, правило «назад»"],
    ], [3.2, 3.2, 3.6, 3.3, 3.2])
    r.table("Преимущества и недостатки подходов", ["Подход", "Преимущества", "Недостатки"], [
        ["TDD", "быстрая обратная связь; высокое покрытие; безопасный рефакторинг; тесты заставляют проектировать слабосвязанный код",
         "не проверяет соответствие требованиям заказчика; тесты нужно поддерживать при изменении интерфейсов; требует дисциплины"],
        ["ATDD", "общее понимание требований до разработки; критерии готовности; проверка системы целиком",
         "нужны встречи всех сторон; тесты медленнее модульных; при ошибке сложнее найти её место"],
        ["BDD", "сценарии понятны не программистам; документация не устаревает; переиспользуемые шаги",
         "дополнительный слой (Gherkin и шаги); риск громоздких сценариев; поддержка определений шагов"],
        ["SDD", "устраняет неоднозначность; удобно задаёт граничные случаи; новый пример – новый тест",
         "сложное поведение трудно уложить в таблицу; разбор таблиц требует кода; таблицы разрастаются"],
    ], [2.0, 7.3, 7.2])
    r.p("Влияние на архитектуру. Требование тестируемости заметно повлияло на структуру продукта. Чтобы "
        "модульные тесты были быстрыми и независимыми, логика плеера отделена от HTTP и не использует "
        "системное время: время передаётся явно через tick, поэтому примеры SDD детерминированы. "
        "Приёмочные тесты потребовали фабрики create_app, создающей изолированный экземпляр приложения для "
        "каждого теста. Иерархия исключений предметной области позволила централизованно сопоставить "
        "ошибки с кодами HTTP. Рефакторинг на этапе TDD, выполненный под защитой тестов, закрыл состояние "
        "плеера от внешнего изменения и устранил дублирование.")
    r.p("Влияние на качество. Тесты каждого следующего этапа запускались вместе с предыдущими, поэтому "
        "добавление режима повтора и хода времени не нарушило уже реализованное поведение – регрессии "
        "обнаруживались бы сразу. Граничные случаи (ровно длительность трека, ровно 3 с, конец плейлиста, "
        "отрицательное время) зафиксированы явно и проверяются автоматически.")
    r.p("Рекомендации по интеграции подходов. Подходы не исключают, а дополняют друг друга, и их удобно "
        "применять как уровни одной пирамиды тестирования:")
    r.items([
        "ATDD – на уровне пользовательской истории: приёмочные критерии как «определение готовности» задачи",
        "BDD – для описания поведения, которое важно обсуждать с бизнесом; сценарии Gherkin служат живой документацией",
        "SDD – для бизнес-правил с большим числом вариантов (расчёты, тарифы, переходы состояний) в виде таблиц",
        "TDD – на уровне реализации каждого класса и функции, обеспечивая быструю обратную связь и безопасный рефакторинг",
        "все наборы тестов запускаются автоматически при каждом изменении (непрерывная интеграция)",
    ])

    # --- Заключение ---------------------------------------------------------
    r.h1("Заключение")
    r.p("В ходе работы изучены подходы TDD, ATDD, BDD и SDD и с их помощью разработан программный продукт "
        "«Музыкальный плеер» (вариант 18). Каждая часть функциональности создана по циклу «тест – падение – "
        "реализация – успешный прогон – рефакторинг»: ядро плеера – через модульные тесты (TDD), REST API – "
        "через приёмочные критерии (ATDD), режим повтора – через сценарии на Gherkin (BDD), ход времени и "
        "правило кнопки «назад» – через таблицу примеров (SDD).")
    r.p("Оценка качества программного продукта: все 58 автоматизированных проверок выполняются успешно, "
        "покрытие операторов составляет 99 %, ошибочные действия пользователя обрабатываются с понятными "
        "сообщениями и корректными кодами ответа. Документация продукта – приёмочные критерии, сценарии "
        "Gherkin и спецификация на примерах – исполняема: она проверяется при каждом прогоне и не может "
        "разойтись с кодом.")
    r.p("Сделан вывод, что TDD обеспечивает надёжность реализации, ATDD и BDD – соответствие ожиданиям "
        "пользователя и общий язык с заказчиком, SDD – однозначность бизнес-правил. Наибольший эффект "
        "даёт их совместное применение на разных уровнях разработки.")

    # --- Источники ----------------------------------------------------------
    r.h1("Список использованных источников")
    for i, src in enumerate([
        "Практическая работа. Подходы для разработки программного обеспечения : методические указания. – М. : РТУ МИРЭА, 2026.",
        "ГОСТ 19.401-78. Единая система программной документации. Текст программы. Требования к содержанию и оформлению.",
        "ГОСТ 34.602-2020. Информационные технологии. Комплекс стандартов на автоматизированные системы. Техническое задание на создание автоматизированной системы.",
        "Бек К. Экстремальное программирование: разработка через тестирование. – СПб. : Питер, 2003. – 224 с.",
        "Аджич Г. Specification by Example: How Successful Teams Deliver the Right Software. – Manning, 2011. – 296 p.",
        "pytest documentation [Электронный ресурс]. – URL: https://docs.pytest.org/ (дата обращения: 31.10.2026).",
        "behave documentation [Электронный ресурс]. – URL: https://behave.readthedocs.io/ (дата обращения: 31.10.2026).",
        "Gherkin Reference [Электронный ресурс]. – URL: https://cucumber.io/docs/gherkin/reference/ (дата обращения: 31.10.2026).",
        "FastAPI. Testing [Электронный ресурс]. – URL: https://fastapi.tiangolo.com/tutorial/testing/ (дата обращения: 31.10.2026).",
    ], 1):
        r.p(f"{i}. {src}")

    # --- Приложения ---------------------------------------------------------
    r.h1("Приложение А. Исходный код программного продукта", new_page=True)
    r.p("Ниже приведён итоговый текст модулей. Нумерация строк соответствует файлам проекта.")
    r.listing("Модуль player/core.py", core, label="А.1")
    r.listing("Модуль player/api.py", api, label="А.2")
    r.p("Для сравнения с итоговой версией приведена первая реализация ядра, полученная на «зелёном» "
        "этапе TDD до рефакторинга.")
    r.listing("Модуль player/core.py после этапа «зелёный» TDD", core_green, label="А.3")

    r.h1("Приложение Б. Модульные, приёмочные и спецификационные тесты", new_page=True)
    r.listing("Модульные тесты tests/unit/test_player.py (TDD)", unit, label="Б.1")
    r.listing("Приёмочные тесты tests/acceptance/test_player_api.py (ATDD)", acceptance, label="Б.2")
    r.listing("Тесты спецификации tests/spec/test_playback_spec.py (SDD)", spec_test, label="Б.3")

    r.h1("Приложение В. Сценарии BDD и определения шагов", new_page=True)
    r.listing("Сценарии features/playback.feature", feature, label="В.1")
    r.listing("Сценарии features/empty_playlist.feature", feature_empty, label="В.2")
    r.listing("Определения шагов features/steps/player_steps.py", steps, label="В.3")
    r.listing("Окружение behave features/environment.py", environment, label="В.4")

    r.h1("Приложение Г. Протокол итогового прогона тестов", new_page=True)
    r.p("Протокол получен командами python -m pytest -v --cov=player --cov-report=term-missing и "
        "python -m behave (файл logs/11_final_all.txt).")
    r.listing("Протокол итогового прогона", (LOGS / "11_final_all.txt").read_text(encoding="utf-8"),
              label="Г.1", numbers=False)

    r.save()
    print(f"Сохранено: {OUTPUT}")


def sys_python() -> str:
    import platform
    return platform.python_version()


def bdd_failure_excerpt() -> list[str]:
    lines = log("07_bdd_red_steps.txt")
    i = next(i for i, ln in enumerate(lines) if "ASSERT FAILED" in ln)
    start = max(j for j in range(i) if "Структура сценария" in lines[j] or "Сценарий" in lines[j])
    return lines[start:i + 3] + ["..."] + lines[-8:]


def final_excerpt() -> list[str]:
    lines = log("11_final_all.txt")
    cov = next(i for i, ln in enumerate(lines) if "tests coverage" in ln)
    behave_summary = lines[-4:]
    return ([lines[0]] + [ln for ln in lines if ln.startswith(("platform", "collecting"))] + ["..."]
            + lines[cov:cov + 9] + ["", "$ python -m behave", "..."] + behave_summary)


if __name__ == "__main__":
    build()
