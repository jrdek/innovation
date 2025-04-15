


from structs import *
from agent_liaison import AgentLiaison
from abc import ABC, abstractmethod
from debug_handler import DFlags
from card_builder import CardStore
import dataclasses as dc
from typing import List


"""
Object responsible for maintaining the state of the game.
"""
class GameManager(ABC):
    _state: GS
    debug: DebugHandler
    liaison: AgentLiaison
    card_store: CardStore


    def _select_turn_draw(self, pid : PlayerId) -> int:
        # find the highest top-card age on player's board.
        # if they have no cards, it's 1.
        turn_draw : Age = 1
        board = self._state.players[pid].board
        for color in Color:
            if len(board[color]) > 0:
                top_age = self.card_store.get(board[color].top()).age
                turn_draw = max(top_age, turn_draw)
        return turn_draw


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
    

    def player_name_and_hand(self, pid: PlayerId) -> Tuple[Tuple[str]]:
        return (self.pid_name(pid),
            tuple(self.card_store.get(cid).name for cid in self.get_player_hand(pid))
        )

    def pid_name(self, pid: PlayerId) -> str:
        return self._state.players[pid].name
    
    
    def update_action_counter(self):
        self._do(self._make_next_action)
        if self.debug[DFlags.GAME_LOG]:
            if not self._state.is_second_action:
                print(f"Now it's {self.active_player_name}'s turn.")


    def turn_draw(self, pid: PlayerId) -> CardId:
        age = self._select_turn_draw(self._state.active_player)
        cards = self.draw(pid, age, 1)
        assert len(cards) == 1
        drawn_card = cards[0]
        return drawn_card


    def reveal(self, card_ids: List[CardId], owner: int):
        self.liaison.reveal_cards(current_state=self._state, card_ids=card_ids, owner=owner)


    def set_active_player(self, pid: PlayerId):
        self._do(lambda state: dc.replace(self._state, active_player=pid))


    def set_winner(self, pid: PlayerId):
        self._do(lambda state: dc.replace(self._state, winner=pid))


    def draw(self, pid: PlayerId, age: Age, amount: int) -> List[CardId]:
        drawn_cards: List[CardId] = []
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
            drawn_card_id = self._state.decks[sought_age][-1]
            self._do(self._remove_top_card_from_deck(sought_age))
            self._do(self._add_card_id_to_player_hand(drawn_card_id, pid))
            if self.debug[DFlags.GAME_LOG]:
                print(f"\t\t\t{self.pid_name(pid)} draws a {self.card_store.get(drawn_card_id).age}:")
                print(f"\t\t\t\t{self.card_store.get(drawn_card_id)}")
            drawn_cards.append(drawn_card_id)
        return drawn_cards


    def meld(self, pid: PlayerId, card_ids: CardIdSequence, zone: PlayerField):
        # TODO: neaten...
        if zone == PlayerField.HAND:
            remove_func = self._remove_card_id_from_player_hand
        elif zone == PlayerField.BOARD:
            remove_func = self._remove_card_id_from_player_board
        elif zone == PlayerField.SCORE_PILE:
            remove_func = self._remove_card_id_from_player_score
        else:
            raise Exception (f"unhandled zone {zone}")
        for card_id in card_ids:
            if self.debug[DFlags.GAME_LOG]:
                print(f"\t\t\t{self.pid_name(pid)} melds {self.card_store.get(card_id)} from their hand.")
            self._do(remove_func(card_id, pid))
            self._do(self._add_card_id_to_player_board(card_id, pid, False))


    def dogma(self, me: PlayerId, card_id: CardId, interpreter: "DogmaInterpreter", is_combo=False):
        # TODO: this feels a little hacky...
        # and there are edge cases when considering mutable gamestates...
        card = self.card_store.get(card_id)
        new_state = interpreter.interpret_card(self, me, card, is_combo)
        self._do(lambda _: new_state)


    def score(self, cards: CardIdSequence, dest_pid: PlayerId, owner_pids: Sequence[PlayerId], src_fields: PlayerField):
        for card, owner_pid, src_field in zip(cards, owner_pids, src_fields):
            self._do(self._score_card_from_pid_field(card, dest_pid, owner_pid, src_field))
            if self.debug[DFlags.GAME_LOG]:
                    print(f"\t\t\t{self.pid_name(dest_pid)} scores {card}. (Total score: {self._state.players[dest_pid].count_score(self.card_store)})")


    def achieve(self, pid: PlayerId):
        # return apply_funcs(state,
        #     [
        #         add_card_id_to_player_achievements(state.achievements[-1], pid),
        #         remove_top_public_achievement
        #     ]
        # )
        # NOTE that the above is just the template for immutable GameStates.
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
    def __init__(self, 
                 liaison: AgentLiaison,
                 debug: DebugHandler,
                 card_store: Optional[CardStore]=None,
                 card_names: Optional[List[str]]=None,
                 state: Optional[ImmutableGameState]=None):
        self.liaison = liaison
        self.debug = debug

        self.card_store = card_store

        # if state exists, then copy it
        if state is not None:
            assert isinstance(state, ImmutableGameState)
            self._state: ImmutableGameState = state
        # otherwise, this is a new game
        else:
            # build decks; make them immutable
            # CHECKME: why is type analysis failing here?
            decks = tuple(tuple(deck) for deck in self.card_store.get_innovation_decks(card_names))
            # new game means completely new GameState and PlayerStates
            self._state: ImmutableGameState = ImmutableGameState(
                debug=debug,
                players=tuple(ImmutablePlayerState(agent.name) for agent in self.liaison.agents),
                decks=decks
            )


    def _do(self, transition: GameStateTransition):
        # here, GameStates are immutable
        self._state = self.apply(self._state, transition)


    @staticmethod
    def apply(state: ImmutableGameState, transition: GameStateTransition) -> ImmutableGameState:
        return transition(state)
    

    # A bunch of pseudo-class-methods implementing atomic card movement.
    # TODO: Should these properly be static? Some depend on the GameState's CardStore.

    @assume_partial
    def _add_card_id_to_pile(self, tuck: bool, pi: ImmutablePile, card_id: CardId) -> ImmutablePile:
        new_cards = self._add_card_id_to_tuple(tuck, pi.cards, card_id)
        return dc.replace(pi, cards=new_cards)


    @assume_partial
    def _add_card_id_to_tuple(self, tuck: bool, xs: Tuple[CardId], card_id: CardId) -> Tuple[CardId]:
        # the top is at index -1
        if tuck:
            return tuple((card_id, *xs))
        else:
            return tuple((*xs, card_id))


    @assume_partial
    def _add_card_id_to_frozenset(self, xs: FrozenSet[CardId], card_id: CardId) -> FrozenSet[CardId]:
        return xs.union(frozenset((card_id,)))


    @assume_partial
    def _container_fail(self, dest : CardIdLoc, card_id: CardId):
        raise TypeError(f"Unhandled container type {type(dest)}")


    def _add_card_id_to_loc(self, card_id: CardId, dest : CardIdLoc, tuck=False) -> CardIdLoc:
        if isinstance(dest, Pile):
            add_func = self._add_card_id_to_pile(tuck)
        elif type(dest) is tuple:
            add_func = self._add_card_id_to_tuple(tuck)
        elif type(dest) is frozenset:
            add_func = self._add_card_id_to_frozenset
        else:
            add_func = self._container_fail

        return apply_funcs(
            card_id,
            [
                add_func(dest)
            ]
        )


    @assume_partial
    def _add_card_id_to_player_hand(self, card_id: CardId, pid : int, state : GameState) -> GameState:
        return dc.replace(state,
            players=tuple(
                p if i != pid else dc.replace(p, 
                    hand=self._add_card_id_to_loc(card_id, dest=p.hand)
                ) for (i,p) in enumerate(state.players)
            )
        )


    @assume_partial
    def _add_card_id_to_player_score(self, card_id: CardId, pid : int, state : GameState) -> GameState:
        return dc.replace(state,
            players=tuple(
                p if i != pid else dc.replace(p, 
                    scored_cards=self._add_card_id_to_loc(card_id, dest=p.scored_cards)
                ) for (i,p) in enumerate(state.players)
            )
        )


    # @assume_partial
    # def _add_card_id_to_player_achievements(self, card_id: CardId, pid : int, state : GameState) -> GameState:
    #     return dc.replace(state,
    #         players=tuple(
    #             p if i != pid else dc.replace(p, 
    #                 achieved_cards=add_card_id_to_loc(card_id, dest=p.achieved_cards)
    #             ) for (i,p) in enumerate(state.players)
    #         )
    #     )


    @assume_partial
    def _add_card_id_to_player_board(self, card_id: CardId, pid : int, tuck : bool, state : GameState) -> GameState:
        card_color = self.card_store.get(card_id).color
        return dc.replace(state,
            players=tuple(
                p if i != pid else dc.replace(p,
                    board=ImmutableBoard(
                        tuple(
                            pile if color != card_color.value
                            else self._add_card_id_to_loc(card_id, p.board[card_color])
                            for color, pile in enumerate(p.board)
                        )
                    )
                ) 
                for (i, p) in enumerate(state.players)
            )
        )


    # @assume_partial
    # def _gain_special_achievement(sa : SpecialAchievement, pid : int, state : GameState) -> GameState:
    #     return dc.replace(state,
    #         players = tuple(
    #             p if i != pid else dc.replace(p, 
    #                 special_achievements=p.special_achievements.union({sa})
    #             ) for (i,p) in enumerate(state.players)
    #         )
    #     )


    @assume_partial
    def _add_card_id_to_deck(self, card_id: CardId, tuck : bool, state : GameState) -> GameState:
        card_age = self.card_store.get(card_id).age
        return dc.replace(state,
            decks=tuple(
                d if i != card_age else self._add_card_id_to_loc(card_id, dest=d, tuck=tuck)
                for (i, d) in enumerate(state.decks)
            )
        )


    @assume_partial
    def _add_card_id_to_global_achievements(self, card_id: CardId, state : GameState) -> GameState:
        return dc.replace(state,
            achievements=self._add_card_id_to_loc(card_id, dest=state.achievements)
        )


    ##### REMOVE A CARD FROM A ZONE #####

    # this is way, way simpler than adding
    def _remove_card_id_from_loc(self, dest : CardIdLoc, card_id: CardId) -> CardIdLoc:
        if all(destcard_id != card_id for destcard_id in dest):
            raise ValueError(f"Card {self.card_store.get(card_id)} not found in "+str(dest))
        try:
            new_dest = type(dest)([c for c in dest if c != card_id])  # TODO: fixme?
            if type(new_dest) is Pile:
                new_dest.splay = dest.splay
            return new_dest
        except:  # TODO specify exception
            self._container_fail(dest, card_id)


    @assume_partial
    def _remove_top_card_from_deck(self, age : Age, state : GameState) -> GameState:
        return dc.replace(state,
            decks=tuple(
                d if i != age else d[:-1]  # no need for the helper func here
                for (i, d) in enumerate(state.decks)
            )
        )


    @assume_partial
    def _remove_top_public_achievement(self, state : GameState) -> GameState:
        return dc.replace(state,
            achievements=state.achievements[:-1]
        )


    @assume_partial
    def _remove_card_id_from_player_hand(self, card_id: CardId, pid : int, state : GameState) -> GameState:
        return dc.replace(state,
            players=tuple(
                p if i != pid else dc.replace(p, 
                    hand=self._remove_card_id_from_loc(p.hand, card_id)
                ) for (i,p) in enumerate(state.players)
            )
        )


    @assume_partial
    def _remove_card_id_from_player_board(self, card_id: CardId, pid : int, state : GameState) -> GameState:
        # TODO: this is slightly cursed
        card_color = self.card_store.get(card_id)
        return dc.replace(state,
            players=tuple(
                p if i != pid else dc.replace(p, 
                    board=ImmutableBoard(
                        tuple(
                            pile if pile.color != card_color
                            else self._remove_card_id_from_loc(p.board[card_color], card_id)
                            for pile in p.board
                        )
                    )
                ) for (i,p) in enumerate(state.players)
            )
        )


    @assume_partial
    def _remove_card_id_from_player_score(self, card_id: CardId, pid : int, state : GameState) -> GameState:
        return dc.replace(state,
            players=tuple(
                p if i != pid else dc.replace(p, 
                    scored_cards=self._remove_card_id_from_loc(p.scored_cards, card_id)
                ) for (i,p) in enumerate(state.players)
            )
        )
    

    def _make_next_action(self, state: GameState) -> GameState:
        is_now_second_action = not state.is_second_action
        now_active_player = state.active_player if is_now_second_action else (state.active_player + 1) % len(state.players)
        return dc.replace(
            state,
            is_second_action=is_now_second_action,
            active_player=now_active_player
        )


    # Draw one card of a given age.
    def _draw_n(self, state : GameState, pid : PlayerId, age : Age) -> Tuple[GameState, Card]:
        # Draw from the lowest non-empty pile >= n

        while (age <= 10) and (len(state.decks[age]) == 0):
            if state.debug[DFlags.GAME_LOG]:
                print(f"The [{age}] pile is empty.")
            age += 1
        if age == 11:
            # the game is over!
            if state.debug[DFlags.GAME_LOG]:
                print(f"{state.players[pid].name} tried to draw an 11!")
            # FIXME: neaten
            state = dc.replace(state, winner=pid)
            return (state, None)
        drawn_card = state.decks[age][-1]

        return (apply_funcs(state,
            [
                self._remove_top_card_from_deck(age),
                self._add_card_id_to_player_hand(drawn_card, pid)
            ]
        ), drawn_card)
    

    @assume_partial
    def _score_card_from_pid_field(self, card: Card, scoring_pid: PlayerId, source_pid: PlayerId, source_field: PlayerField, state: GameState) -> GameState:
        # TODO: make this neater
        # probably means reimplementing remove_card_from_loc
        if source_field == PlayerField.BOARD:
            remove_func = self._remove_card_id_from_player_board(card, source_pid)
        elif source_field == PlayerField.HAND:
            remove_func = self._remove_card_id_from_player_hand(card, source_pid)
        elif source_field == PlayerField.SCORE_PILE:
            remove_func = self._remove_card_id_from_player_score(card, source_pid)
        else:
            remove_func = lambda state: "Can't remove card from PlayerField {field}" // 0
        return apply_funcs(state, [
            remove_func,
            self._add_card_id_to_player_score(card, scoring_pid)
        ])