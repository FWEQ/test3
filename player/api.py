"""REST API музыкального плеера (заглушка для «красных» приёмочных тестов)."""

from fastapi import FastAPI


def create_app() -> FastAPI:
    return FastAPI(title="Музыкальный плеер")
