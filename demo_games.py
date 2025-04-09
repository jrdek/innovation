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
        Player 2 doesn't have enough ideas to share.
        There are no [2]s (or anything higher), so Player 1 tries to draw an 11, ending the game and winning.
    """
    script_p1 = '\n'.join([
        "Writing",
        "draw",
        "dogma Writing"
    ])
    p1 = player_agents.ScriptedAgent("P1", script_p1)

    script_p2 = '\n'.join([
        "TheWheel",  # initial meld
        "dogma TheWheel"
    ])
    p2 = player_agents.ScriptedAgent("P2", script_p2)

    players = [p1, p2]
    expansions = ['test']
    debug_flags = [DFlags.GAME_LOG]

    game = Director(players, expansions, debug_flags)  # TODO: I don't really like this API, actually...
    game.run()


def demo_game_2():
    """
    Game description:
        Two players.
        Loaded cards: all the [1]s.
        Order from top to bottom:
            Metalworking
            Writing
            The Wheel
            Domestication
            CityStates
            Clothing
            Agriculture
            Pottery
            Masonry
            Mysticism
            Code of Laws
            Oars
            Tools
            Archery
            Sailing
    
    Setup:
        Player 1 draws Writing and Metalworking; it melds Metalworking.
        Player 2 draws The Wheel and Domestication; it melds Domestication.
        So Player 2 goes first.

    Play:
    Player 2's turn.
        For Player 2's only action, it uses the dogma on Domestication.
            This is a shared effect. Player 2 has 2 castles.
            Player 1 has 3 castles, so it shares:
                P1 melds the lowest card in its hand (Writing).
                P1 draws a 1 (City States).
            Finally, Player 2 does the effect:
                P2 melds the lowest card in its hand (The Wheel).
                P2 draws a 1 (Clothing).
            Someone shared the action, so P2 takes a turn draw (Agriculture).
    Player 1's turn.
        Player 1 uses the dogma on Metalworking.
            This is a shared effect. Player 1 has 3 castles.
            Player 2 has 5 castles, so it shares:
                P2 draws and reveals a 1 (Pottery).
                It doesn't have a castle, so nothing happens.
            Finally, Player 1 does the effect:
                P1 draws and reveals a 1 (Masonry).
                It has a castle. P1 scores it and repeats.
                P1 draws and reveals a 1 (Mysticism).
                It has a castle. P1 scores it and repeats.
                P1 draws and reveals a 1 (Code of Laws).
                It doesn't have a castle, so nothing happens.
            Someone shared the action, so P1 takes a turn draw (Oars).
        Player 1 uses the dogma on Writing.
            This is a shared effect. Player 1 has 2 ideas.
            Player 2 has 0 ideas, so it doesn't share.
            Finally, Player 1 does the effect:
                P1 tries to draw a 2. This results in drawing an 11.
        Player 1 wins!



    """
    script_p1 = '\n'.join([
        "Metalworking",
        "dogma Metalworking",
        "dogma Writing"
    ])
    p1 = player_agents.ScriptedAgent("P1", script_p1)

    script_p2 = '\n'.join([
        "Domestication",
        "dogma Domestication"
    ])
    p2 = player_agents.ScriptedAgent("P2", script_p2)

    players = [p1, p2]
    expansions = ['test']
    debug_flags = [DFlags.GAME_LOG]

    game = Director(players, expansions, debug_flags)  # TODO: I don't really like this API, actually...
    game.run()


def __main__():
    #demo_game_1()
    demo_game_2()


if __name__ == "__main__":
    __main__()