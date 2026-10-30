import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from player.core import Player  # noqa: E402


def before_scenario(context, scenario):
    context.player = Player()
    context.error = None
