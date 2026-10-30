"""Доменная логика музыкального плеера (заглушка для этапа «красных» тестов TDD)."""

from enum import Enum


class InvalidTrackError(ValueError):
    pass


class EmptyPlaylistError(Exception):
    pass


class PlayerStateError(Exception):
    pass


class PlayerState(Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


class Track:
    def __init__(self, title, artist, duration):
        raise NotImplementedError


class Player:
    def __init__(self):
        raise NotImplementedError
