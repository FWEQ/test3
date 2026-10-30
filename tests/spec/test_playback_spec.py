"""SDD: тесты, построенные по таблице примеров specs/playback_examples.md."""

from pathlib import Path

import pytest

from player.core import EmptyPlaylistError, Player, PlayerStateError, Track

SPEC = Path(__file__).resolve().parents[2] / "specs" / "playback_examples.md"
PLAYLISTS = {
    "стандартный": [Track("Intro", "Band", 180), Track("Song", "Band", 200), Track("Outro", "Band", 150)],
    "пустой": [],
}
ERRORS = {
    "PlayerStateError": PlayerStateError,
    "EmptyPlaylistError": EmptyPlaylistError,
    "ValueError": ValueError,
}
NONE = "—"


def read_examples(path: Path) -> list[dict[str, str]]:
    """Строки таблицы из раздела «Примеры» в виде словарей «колонка → значение»."""
    lines = path.read_text(encoding="utf-8").split("## Примеры", 1)[1].splitlines()
    rows = [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in lines
        if line.startswith("|")
    ]
    header, _separator, *body = rows
    return [dict(zip(header, row)) for row in body]


EXAMPLES = read_examples(SPEC)


def apply(player: Player, action: str) -> None:
    name, *args = action.split()
    getattr(player, name)(*map(int, args))


@pytest.mark.parametrize("ex", EXAMPLES, ids=[f"N{ex['№']}: {ex['Действия']}" for ex in EXAMPLES])
def test_playback_example(ex):
    player = Player()
    player.load(PLAYLISTS[ex["Плейлист"]])
    player.repeat = ex["Повтор"] == "да"
    *setup, last = [a.strip() for a in ex["Действия"].split(";")]

    for action in setup:
        apply(player, action)
    if ex["Ошибка"] == NONE:
        apply(player, last)
    else:
        with pytest.raises(ERRORS[ex["Ошибка"]]):
            apply(player, last)

    title = player.current_track.title if player.current_track else NONE
    assert title == ex["Трек"]
    assert player.state.value == ex["Состояние"]
    assert player.position == int(ex["Позиция"])
