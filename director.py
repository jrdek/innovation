from gameplay import do_turn_draw, meld_from_hand, achieve

# TODO: separate "doing" into an "executor" object...
# then don't reveal atomic_changes to the director.
from atomic_changes import remove_top_card_from_deck, add_card_to_player_hand, remove_card_from_player_hand, add_card_to_player_board

from player_agents import PlayerAgent
import parse_cards
from typing import List, Optional
from collections.abc import Callable
from debug_handler import DebugHandler, DFlags
from dogma_interpreter import DogmaInterpreter
from structs import *
from agent_liaison import AgentLiaison

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
    state: GameState

    def active_player_name(self) -> str:
        return self.state.players[self.active_player].name
    

    def pid_name(self, pid: int) -> str:
        return self.state.players[pid].name
    

    def __init__(self, players : List[PlayerAgent], expansions : List[str], debug_flags : List[DFlags]):
        self.player_agents = players
        self.liaison = AgentLiaison(players)
        self.active_player = 0
        self.is_second_action = True  # player 1 only gets one action
        self.interpreter : DogmaInterpreter = DogmaInterpreter(self.liaison)
        self.all_cards = []
        if debug_flags is None:
            debug_flags = []
        self.debug = DebugHandler(debug_flags)
        for e in expansions:
            self.load_cards(expansion_paths[e])
        # NOTE that the format for `decks` will have to change to support expansions...
        game_players = [get_empty_PlayerState(name=agent.name) for agent in self.player_agents]
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
        # TODO: shuffle decks
        # TODO: populate achievements piles with 1-9 cards
        # TODO: populate special achievements
        # deal two cards to each player. (TODO: restructure where this is done...)
        assert len(game_players) < 8
        draw_actions = []
        cards_drawn = 0
        for pid in range(len(game_players)):
            draw_actions.append(remove_top_card_from_deck(1))
            draw_actions.append(add_card_to_player_hand(game_decks[1][-cards_drawn - 1], pid))
            cards_drawn += 1
            draw_actions.append(remove_top_card_from_deck(1))
            draw_actions.append(add_card_to_player_hand(game_decks[1][-cards_drawn - 1], pid))
            cards_drawn += 1
        self.state = apply_funcs(self.state, draw_actions)
        print("\nDealt initial cards.")
        for player in self.state.players:
            print(f"{player.name}'s hand: [{', '.join(str(card) for card in player.hand)}]")
        print()


    def load_cards(self, path : str):
        # TODO: rework this
        self.all_cards += parse_cards.get_cards_from_path(path)


    def request_choice_of_action(self, pid) -> TurnAction:

        valid_turn_actions = self.get_valid_turn_actions(pid)
        return self.liaison.request_choice_of_one(self.state, pid, valid_turn_actions)


    def request_choice_from_hand(self, pid) -> Card:
        return self.liaison.request_choice_of_one(self.state, pid, self.state.players[pid].hand)
    
    
    def request_choice_from_top_cards(self, pid) -> Card:
        return self.liaison.request_choice_of_one(self.state, pid, self.state.players[pid].get_top_cards())


    def run_initial_melds(self) -> None:
        card_choices = []
        for pid in range(len(self.state.players)):
            card_choices.append(self.request_choice_from_hand(pid))
        print('; '.join(f"{player.name} melds {str(card)}" for player, card in zip(self.state.players, card_choices)) + ".")
        self.active_player = card_choices.index(min(card_choices, key=lambda card: card.name))
        print(f"{self.active_player_name()} goes first.")
        # TODO: executor
        meld_actions = []
        for pid, card in enumerate(card_choices):
            meld_actions.append(remove_card_from_player_hand(card, pid))
            meld_actions.append(add_card_to_player_board(card, pid, False))
        self.state = apply_funcs(self.state, meld_actions)

    
    def interpret(self, card: Card) -> GameState:
        self.interpreter.interpret_card(self.state, self.active_player, card)
        # now its .state is the updated GameState,
        # and its .applied_changes is the "changelog" used to get there.
        return self.interpreter.state


    def do_action(self, pid: int, action: TurnAction):
        # for now at least, this abandons our nice monadic approach
        if action == TurnAction.DRAW:
            if self.debug[DFlags.GAME_LOG]:
                print(f"ACTION: {self.pid_name(pid)} draws.")
            self.state = do_turn_draw(self.state, pid)[0]
        elif action == TurnAction.MELD:
            # request the card
            chosen_card = self.request_choice_from_hand(pid)
            # then meld it.
            self.state = meld_from_hand(self.state, pid, chosen_card)[0]  # TODO: dislike this subscripting
        elif action == TurnAction.DOGMA:
            chosen_card = self.request_choice_from_top_cards(pid)
            if self.debug[DFlags.GAME_LOG]:
                print(f"ACTION: {self.pid_name(pid)} uses the dogma of {chosen_card}.")
            self.state = self.interpret(chosen_card)
        elif action == TurnAction.ACHIEVE:
            # if it's a valid option, it's possible!
            self.state = achieve(self.state, pid)
        else:
            raise Exception(f"Unknown command {action}! There's probably a bug in the PlayerAgent implementation.")

    
    def get_valid_turn_actions(self, pid: int) -> List[TurnAction]:
        actions : List[TurnAction] = [TurnAction.DRAW]  # drawing is always legal (but may end the game)
        player = self.state.players[pid]
        if len(player.hand) > 0:
            actions.append(TurnAction.MELD)
        top_cards = player.get_top_cards()
        if len(top_cards) > 0:
            actions.append(TurnAction.DOGMA)
        # next_achievement_age : int = self.state.achievements[-1].age
        # if any(card.age >= next_achievement_age for card in top_cards) \
        #     and player.count_score() > (5 * next_achievement_age):
        #     actions.append(TurnAction.ACHIEVE)
        return actions
        

    def run(self):

        if self.debug[DFlags.GAME_LOG]:
            print("Starting game.")

        self.run_initial_melds()

        while self.state.winner is None:
            if self.debug[DFlags.GAME_LOG]:
                if not self.is_second_action:
                    print(f"Now it's {self.active_player_name()}'s turn.")
            # the active player chooses an action
            # TODO: specialize this type...
            

            action = self.request_choice_of_action(self.active_player)

            if self.debug[DFlags.TURN_ACTION_CHOICES]:
                print(f"{self.active_player_name()}: {action}")

            # we apply the action
            # (if we wanted to have a stack of applied effects, here's where we'd do it...
            # but not for now.)
            self.do_action(self.active_player, action)

            if self.is_second_action:
                self.active_player = (self.active_player + 1) % len(self.player_agents)
            
            self.is_second_action = not self.is_second_action

        if self.debug[DFlags.GAME_LOG]:
            print(f"{self.pid_name(self.state.winner)} wins!")


