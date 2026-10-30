"""Доменная логика музыкального плеера."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

RESTART_THRESHOLD = 3
"""Если прошло больше секунд, «previous» перезапускает текущий трек."""


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
        self._position = 0
        self.repeat = False

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
    def position(self) -> int:
        """Позиция воспроизведения в текущем треке, секунды."""
        return self._position

    @property
    def current_track(self) -> Track | None:
        return self._playlist[self._index] if self._playlist else None

    def load(self, tracks: Iterable[Track]) -> None:
        self._playlist = list(tracks)
        self._index = 0
        self._state = PlayerState.STOPPED
        self._position = 0

    def play(self) -> None:
        self._require_playlist()
        self._state = PlayerState.PLAYING

    def pause(self) -> None:
        if self._state is not PlayerState.PLAYING:
            raise PlayerStateError("Пауза возможна только во время воспроизведения")
        self._state = PlayerState.PAUSED

    def stop(self) -> None:
        self._state = PlayerState.STOPPED
        self._position = 0

    def tick(self, seconds: int) -> None:
        """Продвигает воспроизведение на заданное число секунд."""
        if seconds < 0:
            raise ValueError("Время не может быть отрицательным")
        if self._state is not PlayerState.PLAYING:
            return
        self._position += seconds
        while self._state is PlayerState.PLAYING and self._position >= self.current_track.duration:
            overflow = self._position - self.current_track.duration
            self.next()
            if self._state is PlayerState.PLAYING:
                self._position = overflow

    def next(self) -> None:
        self._require_playlist()
        if self._index < len(self._playlist) - 1:
            self._switch_to(self._index + 1)
        elif self.repeat:
            self._switch_to(0)
        else:
            self.stop()

    def previous(self) -> None:
        self._require_playlist()
        if self._position > RESTART_THRESHOLD:
            self._switch_to(self._index)
        elif self._index > 0:
            self._switch_to(self._index - 1)
        elif self.repeat:
            self._switch_to(len(self._playlist) - 1)
        else:
            self._switch_to(0)

    def _require_playlist(self) -> None:
        if not self._playlist:
            raise EmptyPlaylistError("Плейлист пуст")

    def _switch_to(self, index: int) -> None:
        """Переключение сохраняет воспроизведение, иначе плеер останавливается."""
        self._index = index
        self._position = 0
        if self._state is not PlayerState.PLAYING:
            self._state = PlayerState.STOPPED
