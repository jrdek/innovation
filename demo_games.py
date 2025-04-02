from director import Director
import player_agents
from debug_handler import DFlags


def demo_game_1():
    # demo game: the only cards loaded are Tools[1] and Calendar[2].
    # players aren't dealt cards initially (unlike the real game).
    script_p1 = [
        "draw",                       # draws Tools, 
        "meld Tools", "dogma Tools"   # melds and then dogma's Tools (TODO)
    ]
    p1 = player_agents.ScriptedAgent(script_p1)

    script_p2 = [
        "draw", "meld Calendar",         # draws Calendar, then melds it
        "draw"                          # wins the game in action 1 by trying to draw an 11
    ]
    p2 = player_agents.ScriptedAgent(script_p2)

    players = [p1, p2]
    expansions = ['test']
    debug_flags = [DFlags.GAME_LOG]

    game = Director(players, expansions, debug_flags)  # TODO: I don't really like this API, actually...
    game.run()


def __main__():
    demo_game_1()


if __name__ == "__main__":
    __main__()