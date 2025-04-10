import game_engine as ge

# TODO: separate "doing" into an "executor" object...
# then don't reveal atomic_changes to the director.
from atomic_changes import *
from debug_handler import DebugHandler, DFlags
from dogma_interpreter import DogmaInterpreter
from structs import *
from agent_liaison import AgentLiaison
from game_manager import GameManager


class Director():
    debug : DebugHandler
    game: GameManager
    interpreter: DogmaInterpreter
    liaison: AgentLiaison
    

    def __init__(self, game: GameManager, liaison: AgentLiaison, interpreter: DogmaInterpreter, debug: DebugHandler):
        self.game = game
        self.liaison = liaison
        self.debug = debug
        self.interpreter = interpreter
        self.num_players = len(self.liaison.agents)


    def run(self):
        if self.debug[DFlags.GAME_LOG]:
            print("Starting game.")

        while self.game.winner is None:
            self.update_action_counter()
            # the active player chooses an action
            action = self.request_choice_of_action(self.game.active_player)
            # the     
            self.do_turn_action(action)
            
        if self.debug[DFlags.GAME_LOG]:
            print(f"{self.game.pid_name(self.game.winner)} wins!")


    def do_turn_action(self, action: TurnAction):
        pid = self.game.active_player
        # by the time this is called, the action is already validated!
        if action == TurnAction.DRAW:
            if self.debug[DFlags.GAME_LOG]:
                print(f"ACTION: {self.pid_name(pid)} draws.")
            self.game.turn_draw(pid)

        elif action == TurnAction.MELD:
            chosen_card: Card = self.request_choice_from_hand(pid)
            if self.debug[DFlags.GAME_LOG]:
                print(f"ACTION: {self.game.pid_name(pid)} melds {chosen_card}.")
            self.game.meld(pid=pid, card=chosen_card, zone=PlayerField.HAND)

        elif action == TurnAction.DOGMA:
            chosen_card = self.request_choice_from_top_cards(pid)
            if self.debug[DFlags.GAME_LOG]:
                print(f"ACTION: {self.game.pid_name(pid)} uses the dogma of {chosen_card}.")
            self.game.dogma(me=pid, card=chosen_card, interpreter=self.interpreter)

        elif action == TurnAction.ACHIEVE:
            self.achieve(pid=pid)

        else:
            raise Exception(f"Unknown command {action}! There's probably a bug in the Liaison implementation.")
            
    
    def update_action_counter(self):
        self.game.update_action_counter()
    

    def request_choice_of_action(self, pid) -> TurnAction:
        valid_turn_actions = self.game.get_valid_turn_actions(pid)
        return self.liaison.request_choice_of_one(self.game, pid, valid_turn_actions)


    def request_choice_from_hand(self, pid) -> Card:
        return self.liaison.request_choice_of_one(self.game, pid, self.game.get_player_hand(pid))
    

    def request_choice_from_top_cards(self, pid) -> Card:
        return self.liaison.request_choice_of_one(self.game, pid, self.game.get_player_top_cards(pid))


    def setup_game(self):
        #self.populate_special_achievements()  # TODO: necessary?
        self._shuffle_decks()
        self._populate_achievements()


    def conduct_initial_melds(self):
        self._deal_initial_cards()
        self._meld_initial_cards()


    def _deal_initial_cards(self):
        assert self.num_players < 8
        for pid in range(self.num_players):
            self.game.draw(pid, age=1, amount=2)
        print("\nDealt initial cards.")
        for pid in range(self.num_players):
            print(f"{self.game.pid_name(pid)}'s hand: [{', '.join(str(card) for card in self.game.get_player_hand(pid))}]")
        print()


    def _meld_initial_cards(self):
        card_choices = []
        for pid in range(self.num_players):
            card_choices.append(self.request_choice_from_hand(pid))
        print('; '.join(f"{self.game.pid_name(pid)} melds {str(card)}" for pid, card in enumerate(card_choices)) + ".")
        # the first player is whoever melded the alphabetically-first card
        first_player = card_choices.index(min(card_choices, key=lambda card: card.name))
        self.game._do(lambda state: dc.replace(state, active_player=first_player))
        print(f"{self.game.active_player_name} goes first.")
        for pid, card in enumerate(card_choices):
            self.game.meld(pid, [card], PlayerField.HAND)


    def _shuffle_decks(self):
        ...  # (unimplemented)

    def _populate_achievements(self):
        ...  # (unimplemented)