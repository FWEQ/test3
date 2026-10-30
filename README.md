# Музыкальный плеер — практическая работа № 3 (вариант 18)

Подходы к разработке через тестирование: TDD, ATDD, BDD, SDD (Specification by Example).
Функции: воспроизведение, пауза, остановка, переключение треков, режим повтора,
ход времени с автопереходом к следующему треку.

## Структура

| Путь | Назначение | Подход |
|------|------------|--------|
| `player/core.py` | доменная логика (`Track`, `Player`) | — |
| `player/api.py` | REST API на FastAPI | — |
| `tests/unit/test_player.py` | модульные тесты | TDD |
| `acceptance/criteria.md` | приёмочные критерии АК-1…АК-8 | ATDD |
| `tests/acceptance/test_player_api.py` | автоматизированные приёмочные тесты | ATDD |
| `features/*.feature`, `features/steps/` | сценарии Gherkin и шаги behave | BDD |
| `specs/playback_examples.md` | спецификация на примерах (таблица) | SDD |
| `tests/spec/test_playback_spec.py` | тесты, генерируемые из таблицы | SDD |
| `logs/` | логи «красных» и «зелёных» прогонов каждого этапа | все |

История этапов (red → green → refactor) видна в `git log`.

## Запуск

```bash
pip install -r requirements.txt

python -m pytest -v                         # TDD + ATDD + SDD
python -m pytest --cov=player --cov-report=term-missing
python -m behave                            # BDD

uvicorn player.api:app --reload             # API, документация: http://127.0.0.1:8000/docs
```

## Отчёт

`report/Отчет_ПР3_Клочков_ФА.docx` (и `.pdf`) собирается скриптом из кода, спецификаций и логов проекта:

```bash
pip install python-docx pillow
python report/build_report.py
soffice --headless --convert-to pdf --outdir report report/Отчет_ПР3_Клочков_ФА.docx
```
