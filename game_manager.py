


from structs import *
from agent_liaison import AgentLiaison
from atomic_changes import *
from abc import ABC, abstractmethod
import game_engine as ge
from debug_handler import DFlags


"""
Object responsible for maintaining the state of the game.
"""
class GameManager(ABC):
    _state: GS
    debug: DebugHandler
    liaison: AgentLiaison


    @abstractmethod
    def _do(self, transition: GameStateTransition):
        # update self.state.
        # depending on strategy, this might be via mutation,
        # or via dataclass copying
        ...


    @staticmethod
    @abstractmethod
    def apply(state: GS, transition: GameStateTransition) -> GS:
        ...  # TODO: do we need this?


    # TODO: consider moving to card_builder.py
    @abstractmethod
    def _build_decks(self) -> Sequence[CardSequence]:
        ...


    # Get the PID of the currently-active player.
    @property
    def active_player(self) -> PlayerId:
        return self._state.active_player
    

    @property
    def players(self) -> Sequence[PlayerState]:
        return self._state.players

    
    @property
    def active_player_name(self) -> str:
        return self.pid_name(self._state.active_player)
    

    @property
    def winner(self):
        return self._state.winner


    def pid_name(self, pid: PlayerId) -> str:
        return self._state.players[pid].name
    
    
    def update_action_counter(self):
        self._do(ge.make_next_action)
        if self.debug[DFlags.GAME_LOG]:
            if not self._state.is_second_action:
                print(f"Now it's {self.active_player_name}'s turn.")


    def turn_draw(self, pid: PlayerId) -> Card:
        age = ge.select_turn_draw(self._state, self._state.active_player)
        cards = self.draw(pid, age, 1)
        return cards[0]


    def reveal(self, cards: List[Card], owner: int):
        self.liaison.reveal_cards(current_state=self._state, cards=cards, owner=owner)


    def set_active_player(self, pid: PlayerId):
        self._do(lambda state: dc.replace(self._state, active_player=pid))


    def set_winner(self, pid: PlayerId):
        self._do(lambda state: dc.replace(self._state, winner=pid))


    def draw(self, pid: PlayerId, age: Age, amount: int) -> List[Card]:
        drawn_cards: List[Card] = []
        sought_age = age
        for _ in range(amount):
            while (sought_age <= 10) and (len(self._state.decks[age]) == 0):
                if self.debug[DFlags.GAME_LOG]:
                    print(f"\t\t\tThe [{sought_age}] pile is empty.")
                sought_age += 1
            if sought_age == 11:
                # game over!
                if self.debug[DFlags.GAME_LOG]:
                    print(f"{self.pid_name(pid)} tried to draw an 11!")
                self.set_winner(pid)
                return drawn_cards
            drawn_card = self._state.decks[sought_age][-1]
            self._do(remove_top_card_from_deck(sought_age))
            self._do(add_card_to_player_hand(drawn_card, pid))
            if self.debug[DFlags.GAME_LOG]:
                print(f"\t\t\t{self.pid_name(pid)} draws a {drawn_card.age}:")
                print(f"\t\t\t\t{drawn_card}")
            drawn_cards.append(drawn_card)
        return drawn_cards


    def meld(self, pid: PlayerId, cards: Sequence[Card], zone: PlayerField):
        # TODO: neaten...
        if zone == PlayerField.HAND:
            remove_func = remove_card_from_player_hand
        elif zone == PlayerField.BOARD:
            remove_func = remove_card_from_player_board
        elif zone == PlayerField.SCORE_PILE:
            remove_func = remove_card_from_player_score
        else:
            raise Exception (f"unhandled zone {zone}")
        for card in cards:
            if self.debug[DFlags.GAME_LOG]:
                print(f"\t\t\t{self.pid_name(pid)} melds {card} from their hand.")
            self._do(remove_func(card, pid))
            self._do(add_card_to_player_board(card, pid, False))


    def dogma(self, me: PlayerId, card: Card, interpreter: "DogmaInterpreter", is_combo=False):
        # TODO: this feels a little hacky...
        # and there are edge cases when considering mutable gamestates...
        new_state = interpreter.interpret_card(self, me, card, is_combo)
        self._do(lambda _: new_state)


    def score(self, cards: Sequence[Card], dest_pid: PlayerId, owner_pids: Sequence[PlayerId], src_fields: PlayerField):
        for card, owner_pid, src_field in zip(cards, owner_pids, src_fields):
            self._do(ge.score_card_from_pid_field(card, dest_pid, owner_pid, src_field))
            if self.debug[DFlags.GAME_LOG]:
                    print(f"\t\t\t{self.pid_name(dest_pid)} scores {card}. (Total score: {self._state.players[dest_pid].count_score()})")


    def achieve(self, pid: PlayerId):
        ...  # TODO later


    def get_player_hand(self, pid) -> Container[Card]:
        return self._state.players[pid].hand
    

    def get_player_top_cards(self, pid) -> Container[Card]:
        return self._state.players[pid].get_top_cards()


    def get_valid_turn_actions(self, pid: PlayerId) -> List[TurnAction]:
        actions : List[TurnAction] = [TurnAction.DRAW]  # drawing is always legal (but may end the game)
        player = self._state.players[pid]
        if len(player.hand) > 0:
            actions.append(TurnAction.MELD)
        top_cards = player.get_top_cards()
        if len(top_cards) > 0:
            actions.append(TurnAction.DOGMA)
        ###(TODO: achievements are currently disabled)
        # next_achievement_age : int = self.state.achievements[-1].age
        # if any(card.age >= next_achievement_age for card in top_cards) \
        #     and player.count_score() > (5 * next_achievement_age):
        #     actions.append(TurnAction.ACHIEVE)
        return actions
    

"""
ImmutableGameState manager.
Implements GameManager. The only differences relate to expecting the GameStates to be
ImmutableGameStates (i.e., ._do() and .apply()).
"""
class IGManager(GameManager): 
    def __init__(self, liaison: AgentLiaison,  debug: DebugHandler, card_store=None, state=None):
        self.liaison = liaison
        self.card_store = card_store
        self.debug = debug
        #self.interpreter = interp
        if state is not None:
            assert isinstance(state, ImmutableGameState)
            self._state: ImmutableGameState = state
        else:
            decks = self._build_decks()
            self._state: ImmutableGameState = ImmutableGameState(
                debug=debug,
                players=[ImmutablePlayerState(agent.name) for agent in self.liaison.agents],
                decks=decks
            )


    def _do(self, transition: GameStateTransition):
        # this implementation: GameStates are immutable
        self._state = self.apply(self._state, transition)


    @staticmethod
    def apply(state: ImmutableGameState, transition: GameStateTransition) -> ImmutableGameState:
        return transition(state)


    def _build_decks(self) -> Tuple[ImmutableCardSequence]:
        decks: List[List[Card]] = [[] for _ in range(11)]  # the 0 deck should always be empty
        for card in self.card_store.cards:
            decks[card.age].append(card)
        # make immutable
        return tuple(tuple(card for card in deck) for deck in decks)