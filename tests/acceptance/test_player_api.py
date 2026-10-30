"""ATDD: приёмочные тесты REST API плеера (критерии — acceptance/criteria.md)."""

import pytest
from fastapi.testclient import TestClient

from player.api import create_app

PLAYLIST = {
    "tracks": [
        {"title": "Intro", "artist": "Band", "duration": 180},
        {"title": "Song", "artist": "Band", "duration": 200},
        {"title": "Outro", "artist": "Band", "duration": 150},
    ]
}


@pytest.fixture
def client():
    return TestClient(create_app())


@pytest.fixture
def loaded(client):
    assert client.put("/playlist", json=PLAYLIST).status_code == 200
    return client


def press(client, button):
    return client.post(f"/player/{button}")


def test_ac1_load_playlist(client):
    response = client.put("/playlist", json=PLAYLIST)

    assert response.status_code == 200
    body = response.json()
    assert len(body["playlist"]) == 3
    assert body["track"]["title"] == "Intro"
    assert body["state"] == "stopped"


def test_ac2_play_starts_first_track(loaded):
    response = press(loaded, "play")

    assert response.status_code == 200
    assert response.json()["state"] == "playing"
    assert response.json()["track"]["title"] == "Intro"


def test_ac3_pause_and_resume(loaded):
    press(loaded, "play")

    paused = press(loaded, "pause").json()
    assert paused["state"] == "paused"

    resumed = press(loaded, "play").json()
    assert resumed["state"] == "playing"
    assert resumed["track"]["title"] == "Intro"


def test_ac4_switch_tracks(loaded):
    press(loaded, "play")

    after_next = press(loaded, "next").json()
    assert (after_next["track"]["title"], after_next["state"]) == ("Song", "playing")

    after_previous = press(loaded, "previous").json()
    assert (after_previous["track"]["title"], after_previous["state"]) == ("Intro", "playing")


def test_ac5_end_of_playlist_stops(loaded):
    press(loaded, "play")
    press(loaded, "next")
    press(loaded, "next")

    status = press(loaded, "next").json()

    assert status["state"] == "stopped"
    assert status["track"]["title"] == "Outro"


def test_ac6_play_with_empty_playlist(client):
    response = press(client, "play")

    assert response.status_code == 400
    assert response.json()["detail"] == "Плейлист пуст"


def test_ac7_pause_when_stopped(loaded):
    response = press(loaded, "pause")

    assert response.status_code == 409
    assert "Пауза возможна только" in response.json()["detail"]
    assert loaded.get("/player").json()["state"] == "stopped"


def test_ac8_invalid_track_keeps_previous_playlist(loaded):
    bad = {"tracks": [{"title": "Broken", "artist": "Band", "duration": 0}]}

    response = loaded.put("/playlist", json=bad)

    assert response.status_code == 400
    status = loaded.get("/player").json()
    assert [t["title"] for t in status["playlist"]] == ["Intro", "Song", "Outro"]
