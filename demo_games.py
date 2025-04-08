from director import Director
import player_agents
from debug_handler import DFlags

# TODO: flexible framework for setting up deterministic games
def demo_game_1():
    """
    Game description:
        Two players.
        Loaded cards: all the [1]s.

        Player 1 draws Writing and Metalworking; it melds Writing.
        Player 2 draws The Wheel and Domestication; it melds The Wheel.
        So Player 2 goes first.

        For Player 2's only action, it dogmas The Wheel.
            This is a shared action, but Player 1 doesn't have enough castles to share.
            Player 2 draws two [1]s.
        
        Now it's Player 1's turn.
        For its first action, it draws a card (a [1]).
        For its second action, it dogmas Writing.
        There are no [2]s (or anything higher), so Player 1 tries to draw an 11, ending the game and winning.
    """
    script_p1 = '\n'.join([
        "Writing",
        "draw",
        "dogma Writing"
    ])
    p1 = player_agents.ScriptedAgent(script_p1)

    script_p2 = '\n'.join([
        "TheWheel",  # initial meld
        "dogma TheWheel"
    ])
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