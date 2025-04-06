from gameplay import do_turn_draw, meld_from_hand, achieve, use_dogma
from game_state import GameState, build_decks, get_empty_PlayerState
from player_agents import PlayerAgent
import parse_cards
from typing import List, Optional
from game_state import Card
from collections.abc import Callable
from debug_handler import DebugHandler, DFlags


expansion_paths = {
    'base': 'cards/base_game.cards',
    'test': 'cards/testing.cards'
}


class Director():
    player_agents : List[PlayerAgent]
    active_player : int
    card_list_path : str
    all_cards : List[Card]
    debug : DebugHandler

    def __init__(self, players : List[PlayerAgent], expansions : List[str], debug_flags : List[DFlags]):
        self.player_agents = players
        self.active_player = 0
        self.is_second_action = True  # player 1 only gets one action
        self.all_cards = []
        if debug_flags is None:
            debug_flags = []
        self.debug = DebugHandler(debug_flags)
        for e in expansions:
            self.load_cards(expansion_paths[e])
        # NOTE that the format for `decks` will have to change to support expansions...
        game_players = [get_empty_PlayerState() for _ in players]
        game_decks = build_decks(self.all_cards)
        game_achievements = []
        game_special_achievements = []
        game_winner = None
        self.state = GameState(
            game_players,
            game_decks,
            game_achievements,
            game_special_achievements,
            game_winner,
            self.debug
            )
        self.state.setup_shuffle()
        # TODO: populate achievements piles with 1-9 cards
        # TODO: populate special achievements
        # TODO: deal two cards to each player


    def load_cards(self, path : str):
        # TODO: rework this
        self.all_cards += parse_cards.get_cards_from_path(path)


    def do_action(self, action_id : str, action_args : List[str]):
        # for now at least, this abandons our nice monadic approach
        if action_id == "draw":
            self.state = do_turn_draw(self.state, self.active_player)
        elif action_id == "meld":
            # find the card
            found = False
            for card in self.state.players[self.active_player].hand:
                if card.name == action_args[0]:
                    self.state = meld_from_hand(self.state, self.active_player, card)
                    found = True
                    break
            if not found:
                raise Exception(f"Player {self.active_player}'s hand doesn't contain {action_args[0]}")
        elif action_id == "dogma":
            # obvious TODO which I haven't resolved because it's 5am: 
            # decide whether these fn's take strings or Cards
            self.state = use_dogma(self.state, self.active_player, action_args[0])
        elif action_id == "achieve":
            raise Exception("Not yet implemented")
        else:
            raise Exception("Unknown command! There's probably a bug in the PlayerAgent implementation.")


    def run(self):
        if self.debug[DFlags.GAME_LOG]:
            print("Starting game.")

        while self.state.winner is None:
            # the active player chooses an action
            # TODO: specialize this type...
            action_id, action_args = self.player_agents[self.active_player].choose_turn_action()

            if self.debug[DFlags.TURN_ACTION_CHOICES]:
                print(f"Player {self.active_player+1}: {action_id} {action_args}")

            # we apply the action
            # (if we wanted to have a stack of applied effects, here's where we'd do it...
            # but not for now.)
            self.do_action(action_id, action_args)

            if self.is_second_action:
                self.active_player = (self.active_player + 1) % len(self.player_agents)
            
            self.is_second_action = not self.is_second_action

        if self.debug[DFlags.GAME_LOG]:
            print(f"Player {self.state.winner + 1} wins!")


