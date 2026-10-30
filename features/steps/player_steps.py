from behave import given, step, then

from player.core import EmptyPlaylistError, PlayerState, PlayerStateError, Track

STATES = {
    "воспроизведение": PlayerState.PLAYING,
    "пауза": PlayerState.PAUSED,
    "остановлен": PlayerState.STOPPED,
}
REPEAT = {"включён": True, "выключен": False}


@given("треки загружены в плеер:")
def step_load_tracks(context):
    context.player.load(
        Track(row["название"], row["исполнитель"], int(row["длительность"]))
        for row in context.table
    )


@given("плейлист пуст")
def step_empty_playlist(context):
    context.player.load([])


@given('плеер воспроизводит трек "{title}"')
def step_playing_track(context, title):
    player = context.player
    player.play()
    for _ in player.playlist:
        if player.current_track.title == title:
            return
        player.next()
    raise AssertionError(f'Трек "{title}" отсутствует в плейлисте')


@given("режим повтора {mode}")
def step_repeat_mode(context, mode):
    context.player.repeat = REPEAT[mode]


@step('я нажимаю "{button}"')
def step_press(context, button):
    try:
        getattr(context.player, button)()
    except (EmptyPlaylistError, PlayerStateError) as exc:
        context.error = exc


@then("начинается воспроизведение")
def step_is_playing(context):
    assert context.player.state is PlayerState.PLAYING, context.player.state


@then("воспроизведение приостановлено")
def step_is_paused(context):
    assert context.player.state is PlayerState.PAUSED, context.player.state


@then('плеер в состоянии "{state}"')
def step_state(context, state):
    assert context.player.state is STATES[state], context.player.state


@then('звучит трек "{title}"')
def step_track_sounds(context, title):
    assert context.player.state is PlayerState.PLAYING, context.player.state
    assert context.player.current_track.title == title, context.player.current_track


@then('текущий трек "{title}"')
def step_current_track(context, title):
    assert context.player.current_track.title == title, context.player.current_track


@then('плеер сообщает об ошибке "{message}"')
def step_error(context, message):
    assert context.error is not None, "Ошибка не возникла"
    assert str(context.error) == message, context.error
