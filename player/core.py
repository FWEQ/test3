"""Доменная логика музыкального плеера."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class InvalidTrackError(ValueError):
    """Некорректные метаданные трека."""


class EmptyPlaylistError(Exception):
    """Операция требует непустого плейлиста."""


class PlayerStateError(Exception):
    """Операция недопустима в текущем состоянии плеера."""


class PlayerState(Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


@dataclass(frozen=True)
class Track:
    title: str
    artist: str
    duration: int

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise InvalidTrackError("Название трека не может быть пустым")
        if self.duration <= 0:
            raise InvalidTrackError("Длительность трека должна быть положительной")


class Player:
    def __init__(self) -> None:
        self._playlist: list[Track] = []
        self._index = 0
        self._state = PlayerState.STOPPED

    @property
    def playlist(self) -> list[Track]:
        return list(self._playlist)

    @property
    def state(self) -> PlayerState:
        return self._state

    @property
    def index(self) -> int:
        return self._index

    @property
    def current_track(self) -> Track | None:
        return self._playlist[self._index] if self._playlist else None

    def load(self, tracks: Iterable[Track]) -> None:
        self._playlist = list(tracks)
        self._index = 0
        self._state = PlayerState.STOPPED

    def play(self) -> None:
        self._require_playlist()
        self._state = PlayerState.PLAYING

    def pause(self) -> None:
        if self._state is not PlayerState.PLAYING:
            raise PlayerStateError("Пауза возможна только во время воспроизведения")
        self._state = PlayerState.PAUSED

    def stop(self) -> None:
        self._state = PlayerState.STOPPED

    def next(self) -> None:
        self._require_playlist()
        if self._index == len(self._playlist) - 1:
            self._state = PlayerState.STOPPED
        else:
            self._switch_to(self._index + 1)

    def previous(self) -> None:
        self._require_playlist()
        self._switch_to(max(self._index - 1, 0))

    def _require_playlist(self) -> None:
        if not self._playlist:
            raise EmptyPlaylistError("Плейлист пуст")

    def _switch_to(self, index: int) -> None:
        """Переключение сохраняет воспроизведение, иначе плеер останавливается."""
        self._index = index
        if self._state is not PlayerState.PLAYING:
            self._state = PlayerState.STOPPED
