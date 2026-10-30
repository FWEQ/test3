"""Доменная логика музыкального плеера."""

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
        if not title.strip():
            raise InvalidTrackError("Название трека не может быть пустым")
        if duration <= 0:
            raise InvalidTrackError("Длительность трека должна быть положительной")
        self.title = title
        self.artist = artist
        self.duration = duration

    def __eq__(self, other):
        return (self.title, self.artist, self.duration) == (other.title, other.artist, other.duration)


class Player:
    def __init__(self):
        self.playlist = []
        self.index = 0
        self.state = PlayerState.STOPPED

    @property
    def current_track(self):
        if not self.playlist:
            return None
        return self.playlist[self.index]

    def load(self, tracks):
        self.playlist = list(tracks)
        self.index = 0
        self.state = PlayerState.STOPPED

    def play(self):
        if not self.playlist:
            raise EmptyPlaylistError("Плейлист пуст")
        self.state = PlayerState.PLAYING

    def pause(self):
        if self.state != PlayerState.PLAYING:
            raise PlayerStateError("Пауза возможна только во время воспроизведения")
        self.state = PlayerState.PAUSED

    def stop(self):
        self.state = PlayerState.STOPPED

    def next(self):
        if not self.playlist:
            raise EmptyPlaylistError("Плейлист пуст")
        if self.index == len(self.playlist) - 1:
            self.state = PlayerState.STOPPED
            return
        self.index += 1
        if self.state != PlayerState.PLAYING:
            self.state = PlayerState.STOPPED

    def previous(self):
        if not self.playlist:
            raise EmptyPlaylistError("Плейлист пуст")
        if self.index > 0:
            self.index -= 1
        if self.state != PlayerState.PLAYING:
            self.state = PlayerState.STOPPED
