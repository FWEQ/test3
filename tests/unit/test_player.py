"""TDD: модульные тесты доменной логики плеера."""

import pytest

from player.core import (
    EmptyPlaylistError,
    InvalidTrackError,
    Player,
    PlayerState,
    PlayerStateError,
    Track,
)


@pytest.fixture
def tracks():
    return [
        Track("Intro", "Band", 180),
        Track("Song", "Band", 200),
        Track("Outro", "Band", 150),
    ]


@pytest.fixture
def player(tracks):
    p = Player()
    p.load(tracks)
    return p


# --- Трек ---------------------------------------------------------------

def test_track_stores_metadata():
    track = Track("Intro", "Band", 180)
    assert (track.title, track.artist, track.duration) == ("Intro", "Band", 180)


@pytest.mark.parametrize("title", ["", "   "], ids=["empty", "spaces"])
def test_track_requires_title(title):
    with pytest.raises(InvalidTrackError):
        Track(title, "Band", 180)


@pytest.mark.parametrize("duration", [0, -5])
def test_track_requires_positive_duration(duration):
    with pytest.raises(InvalidTrackError):
        Track("Intro", "Band", duration)


# --- Загрузка плейлиста -------------------------------------------------

def test_new_player_is_stopped_and_empty():
    p = Player()
    assert p.state is PlayerState.STOPPED
    assert p.current_track is None
    assert p.playlist == []


def test_load_makes_first_track_current(player, tracks):
    assert player.playlist == tracks
    assert player.current_track == tracks[0]
    assert player.state is PlayerState.STOPPED


def test_load_resets_playback(player, tracks):
    player.play()
    player.next()
    player.load(tracks[::-1])
    assert player.state is PlayerState.STOPPED
    assert player.current_track == tracks[2]


def test_load_copies_playlist(tracks):
    p = Player()
    p.load(tracks)
    tracks.clear()
    assert len(p.playlist) == 3


# --- Воспроизведение и пауза --------------------------------------------

def test_play_starts_playback(player, tracks):
    player.play()
    assert player.state is PlayerState.PLAYING
    assert player.current_track == tracks[0]


def test_play_with_empty_playlist_raises():
    with pytest.raises(EmptyPlaylistError):
        Player().play()


def test_play_twice_keeps_playing(player):
    player.play()
    player.play()
    assert player.state is PlayerState.PLAYING


def test_pause_while_playing(player):
    player.play()
    player.pause()
    assert player.state is PlayerState.PAUSED


@pytest.mark.parametrize(
    "prepare",
    [lambda p: None, lambda p: (p.play(), p.pause())],
    ids=["stopped", "paused"],
)
def test_pause_when_not_playing_raises(player, prepare):
    prepare(player)
    with pytest.raises(PlayerStateError):
        player.pause()


def test_play_after_pause_resumes_same_track(player, tracks):
    player.play()
    player.next()
    player.pause()
    player.play()
    assert player.state is PlayerState.PLAYING
    assert player.current_track == tracks[1]


def test_stop_stops_playback(player):
    player.play()
    player.stop()
    assert player.state is PlayerState.STOPPED


# --- Переключение треков ------------------------------------------------

def test_next_switches_to_following_track(player, tracks):
    player.next()
    assert player.current_track == tracks[1]


def test_next_keeps_playing(player, tracks):
    player.play()
    player.next()
    assert player.state is PlayerState.PLAYING
    assert player.current_track == tracks[1]


def test_next_while_paused_stops(player, tracks):
    player.play()
    player.pause()
    player.next()
    assert player.state is PlayerState.STOPPED
    assert player.current_track == tracks[1]


def test_next_on_last_track_stops_playback(player, tracks):
    player.play()
    player.next()
    player.next()
    player.next()
    assert player.current_track == tracks[2]
    assert player.state is PlayerState.STOPPED


def test_previous_switches_back(player, tracks):
    player.play()
    player.next()
    player.previous()
    assert player.current_track == tracks[0]
    assert player.state is PlayerState.PLAYING


def test_previous_on_first_track_stays_on_first(player, tracks):
    player.play()
    player.previous()
    assert player.current_track == tracks[0]
    assert player.state is PlayerState.PLAYING


@pytest.mark.parametrize("action", ["next", "previous"])
def test_switching_with_empty_playlist_raises(action):
    with pytest.raises(EmptyPlaylistError):
        getattr(Player(), action)()
