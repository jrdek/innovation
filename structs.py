from __future__ import annotations

from enum import Enum, auto
from typing import TypeAlias, Dict, TypeVar, Optional, Sequence, Tuple, Container, FrozenSet, Set, Union
from dataclasses import dataclass
from collections.abc import Callable
from functools import partial
from inspect import signature
from debug_handler import DebugHandler
from abc import ABC
from collections import Counter


# (i just want to be able to print enums as strs)
# this is in certain versions of Python but not others
class StrEnum(Enum):
    def __str__(self):
        return self.name


class TurnAction(StrEnum):
    DRAW = auto()
    MELD = auto()
    DOGMA = auto()
    ACHIEVE = auto()


class Color(StrEnum):
    RED = 0
    YELLOW = 1
    GREEN = 2
    BLUE = 3
    PURPLE = 4


class Icon(StrEnum):
    CROWN = auto()
    LEAF = auto()
    IDEA = auto()
    CASTLE = auto()
    FACTORY = auto()
    CLOCK = auto()
    HEX = auto()


class Splay(Enum):
    NONE = 0
    LEFT = 1
    RIGHT = 2
    UP = 3
"""
Splaying reveals icons, indexed as follows:
 --------------------------------
|                CARD TITLE      |
|   1                            |
|            (dogmas n stuff)    |
|                                |
|   2          3          4      |
|                                |
 --------------------------------
 (The remaining two spots on the 2x3 grid are used in some expansions.)
"""
splay_indices = (
    (),        # NONE
    (4),       # LEFT
    (1, 2),    # RIGHT
    (2, 3, 4)  # UP
)


class PlayerField(Enum):
    HAND = auto()
    BOARD = auto()
    SCORE_PILE = auto()
    ACHIEVEMENTS_PILE = auto()


# let's print out cards in their colors :)
card_colors : Dict[Color, str] = {
    Color.RED: '\033[91m',
    Color.YELLOW: '\033[93m',
    Color.GREEN: '\033[92m',
    Color.BLUE: '\033[94m',
    Color.PURPLE: '\033[95m'
}
color_end = '\033[0m'


def colored_str(s : str, c : Color) -> str:
    return card_colors[c] + s + color_end


# A DEffect corresponds to `dogma_effect` in the grammar:
# - the `effect_header` is stored as DEffect.key_icon and DEffect.is_demand
# - the `stmts` are stored as a list of DogmaActions
@dataclass(frozen=True)
class DEffect:
    is_demand : bool
    key_icon : Icon
    effects : "Stmts"  # ughhhhh FIXME i do not want to deal with forward declaration in *Python*

    def __str__(self):
        INDENT = '  '
        s = ''
        kind = "Demand" if self.is_demand else "Shared"
        s += f"- {kind} ({self.key_icon}):\n"
        for action in self.effects:
            for line in str(action).split("\n"):
                s += INDENT + line + "\n"
        return s


@dataclass(frozen=True)
class Card:
    name : str
    color : Color
    age : int
    icons : Tuple[Icon]
    dogmata : Tuple[DEffect]

    # card names are unique -- if two cards have the 
    # same name, then they are equal
    def __eq__(self, other):
        if type(other) is not Card: return False
        return self.name == other.name
    
    def __lt__(self, other):
        if type(other) is not Card: return False
        return self.age < other.age
    
    def __le__(self, other):
        if type(other) is not Card: return False
        return self.age <= other.age
    
    def detailed_str(self) -> str:
        return \
        f"<{colored_str(f'[{self.age}] {self.name}', self.color)}>\n" + \
        str(self.icons[0]) + "\n" + \
        '\t'.join(str(i) for i in self.icons[1:]) + "\n" + \
        "\n".join(str(d) for d in self.dogmata)

    def __str__(self) -> str:
        return f"<{card_colors[self.color]}[{self.age}] {self.name}{color_end}>"


@dataclass(frozen=True)
class SpecialAchievement:
    name : str
    meets_cond : Callable[[GameState, int], bool]
    # special achievements don't need to know who owns them


class Pile(ABC, Sequence):
    cards : Container[CardId]
    splay : Splay
    
    def __contains__(self, item) -> bool:
        return item in self.cards

    def __len__(self) -> int:
        return len(self.cards)
    
    def top(self) -> Card:
        return self.cards[-1]
    
    def bottom(self) -> Card:
        return self.cards[0]

    def count_icon(self, card_store: "CardStore", targ_icon : Icon) -> int:
        # TODO: test thoroughly
        total : int = 0
        for card_no, card_id in enumerate(self.cards):
            card = card_store.get(card_id)
            if card_no == len(self.cards)-1:
                total += card.icons.count(targ_icon)
            else:
                total += len([card.icons[i] for i in splay_indices[self.splay] if card.icons[i] is targ_icon]) 
        return total
    

@dataclass(frozen=True)
class ImmutablePile(Pile):
    cards: Tuple[Card] = ()  # (O(n) retrieval, but it's OK: piles are tractably small)

    def __getitem__(self, item):
        return item in self.cards


# A PlayerState is a full-detail snapshot of a player's hand/board/etc.
class PlayerState(ABC):
    name: str
    hand : Container[Card]
    scored_cards : Container[Card]
    achieved_cards : Container[Card]
    special_achievements : Container[SpecialAchievement]
    board : Board


    @property
    def fields(self) -> Dict[PlayerField, Container]:
        return {
            PlayerField.ACHIEVEMENTS_PILE: self.achieved_cards,
            PlayerField.BOARD: self.board,
            PlayerField.HAND: self.hand,
            PlayerField.SCORE_PILE: self.scored_cards
        }


    def count_achievements(self) -> int:
        return len(self.achieved_cards)
    

    def count_score(self, card_store: "CardStore") -> int:
        return sum(card_store.get(card_id).age for card_id in self.scored_cards)
    

    def get_score_profile(self, card_store: "CardStore") -> Counter[int]:
        return Counter([card_store.get(card_id).age for card_id in self.scored_cards])
    

    def count_icon(self, card_store: "CardStore", targ_icon : Icon) -> int:
        return sum(pile.count_icon(card_store, targ_icon) for pile in self.board.piles)
    

    def get_top_cards(self) -> Tuple[Card]:
        out = []
        for color in Color:
            if len(self.board[color]) > 0:
                out.append(self.board[color].top())
        return out
    

class Board(ABC):
    piles: Container[Pile]


    def __getitem__(self, item) -> Pile:
        # assert isinstance(item, Color)
        if isinstance(item, Color):
            item = item.value  # TODO: this feels cheeky...
        return self.piles[item]
    

@dataclass(frozen=True)
class ImmutableBoard(Board):
    piles: Tuple[ImmutablePile] = tuple(ImmutablePile() for _ in range(len(Color)))


@dataclass(frozen=True)
class ImmutablePlayerState(PlayerState):
    name: str
    hand: FrozenSet[Card] = frozenset()
    scored_cards: FrozenSet[Card] = frozenset()
    achieved_cards: FrozenSet[Card] = frozenset()
    special_achievements: FrozenSet[SpecialAchievement] = frozenset()
    board: ImmutableBoard = ImmutableBoard()


class GameState(ABC):
    debug: DebugHandler
    players: Sequence[PlayerState]
    active_player: PlayerId = 0
    is_second_action: bool = False
    decks: Sequence[CardIdSequence]
    achievements: CardIdSequence
    special_achievements: Tuple[SpecialAchievement]
    winner: Optional[PlayerId]


@dataclass(frozen=True)
class ImmutableGameState(GameState):
    debug: DebugHandler
    players: Tuple[ImmutablePlayerState] = ()
    active_player: PlayerId = 0
    is_second_action: bool = False
    decks: Tuple[ImmutableCardIdSequence] = ()
    achievements: Tuple[Card] = ()
    special_achievements: Tuple[SpecialAchievement] = ()
    winner : Optional[PlayerId] = None


@dataclass
class EvaluatedZonedSelectionStrategy:
    num: int
    selection_lambda: Callable[[Container[T]], T]
    pid: PlayerId
    field: PlayerField


T = TypeVar("T")
GS = TypeVar("GS", bound=GameState)

SetLike: TypeAlias[T] = Set[T] | FrozenSet[T]  # frozensets aren't sets!

PlayerId = int
CardId = int
Age = int

Dogma = Tuple[DEffect]
GameStateTransition = Callable[[GS], GS]
CardProp = Callable[[Card], bool]
CardsProp = Callable[[Container[Card]], bool]

CardIdLoc = Container[CardId]
CardIdSequence = Sequence[CardId]
ImmutableCardIdSequence = Tuple[CardId]
CardIdSet = SetLike[CardId]
ImmutableCardIdSet = FrozenSet[CardId]


# finally, a couple utility functions...

# TODO: What's a better type signature for this?
def apply_funcs(t : any, fs : Sequence[Callable]) -> any:
    for f in fs:
        t = f(t)
    return t


# decorator to assume that a function is partial if not all args
# are supplied.
# NOTE: this might break if func uses *args/**kwargs
def assume_partial(func):
    num_params = len(signature(func).parameters)
    def wrapper(*args):
        if len(args) < num_params:
            # TODO: is this bad?
            subfunc = assume_partial(partial(func, *args))
            return subfunc
        else:
            return func(*args)  # throws error if too many args
    return wrapper