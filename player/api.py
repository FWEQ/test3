"""REST API музыкального плеера — тонкий слой поверх доменной логики."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from player.core import (
    EmptyPlaylistError,
    InvalidTrackError,
    Player,
    PlayerStateError,
    Track,
)


class TrackIn(BaseModel):
    title: str
    artist: str
    duration: int


class PlaylistIn(BaseModel):
    tracks: list[TrackIn]


ERROR_CODES = {
    EmptyPlaylistError: 400,
    InvalidTrackError: 400,
    PlayerStateError: 409,
}


def _track_to_dict(track: Track | None) -> dict | None:
    if track is None:
        return None
    return {"title": track.title, "artist": track.artist, "duration": track.duration}


def _status(player: Player) -> dict:
    return {
        "state": player.state.value,
        "index": player.index,
        "track": _track_to_dict(player.current_track),
        "playlist": [_track_to_dict(t) for t in player.playlist],
    }


def create_app(player: Player | None = None) -> FastAPI:
    app = FastAPI(title="Музыкальный плеер")
    player = player or Player()

    for error, code in ERROR_CODES.items():
        app.add_exception_handler(error, _error_handler(code))

    @app.get("/player")
    def get_status() -> dict:
        return _status(player)

    @app.put("/playlist")
    def load_playlist(body: PlaylistIn) -> dict:
        player.load([Track(t.title, t.artist, t.duration) for t in body.tracks])
        return _status(player)

    actions = {
        "play": player.play,
        "pause": player.pause,
        "stop": player.stop,
        "next": player.next,
        "previous": player.previous,
    }
    for name, action in actions.items():
        app.post(f"/player/{name}", name=name)(_action_endpoint(player, action))

    return app


def _error_handler(code: int):
    async def handle(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=code, content={"detail": str(exc)})

    return handle


def _action_endpoint(player: Player, action):
    def endpoint() -> dict:
        action()
        return _status(player)

    return endpoint


app = create_app()
