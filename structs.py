from __future__ import annotations

from enum import Enum, auto
from typing import List, Dict, TypeVar, Deque, Optional
from dataclasses import dataclass
from collections.abc import Callable
from functools import partial
from inspect import signature
from debug_handler import DFlags, DebugHandler
from collections import Counter, deque

class StrEnum(Enum):
    def __str__(self):
        return self.name


# TODO: What's a better type signature for this?
def apply_funcs(t : any, fs : List[Callable]) -> any:
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


T = TypeVar("T")


class TurnAction(StrEnum):
    DRAW = auto()
    MELD = auto()
    DOGMA = auto()
    ACHIEVE = auto()


class Color(StrEnum):
    RED = auto()
    YELLOW = auto()
    GREEN = auto()
    BLUE = auto()
    PURPLE = auto()


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
@dataclass
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

Dogma = List[DEffect]

@dataclass
class Card:
    name : str
    color : Color
    age : int
    icons : List[Icon]
    dogmata : List[DEffect]

    # card names are unique -- if two cards have the 
    # same name, then they are equal
    def __eq__(self, other):
        if type(other) is not Card: return False
        return self.name == other.name
    
    def detailed_str(self) -> str:
        return \
        f"<{colored_str(f'[{self.age}] {self.name}', self.color)}>\n" + \
        str(self.icons[0]) + "\n" + \
        '\t'.join(str(i) for i in self.icons[1:]) + "\n" + \
        "\n".join(str(d) for d in self.dogmata)

    def __str__(self) -> str:
        return f"<{card_colors[self.color]}[{self.age}] {self.name}{color_end}>"


@dataclass
class SpecialAchievement:
    name : str
    meets_cond : Callable[[GameState, int], bool]
    # special achievements don't need to know who owns them


# NOTE: Initially, Pile inherited from deque.
# It ended up being a bit easier to just have the container of cards be a field
# which is accessed transparently via __getitem__ and __contains__.
# TODO: Think more about this choice.
@dataclass
class Pile:
    cards : Deque[Card]
    splay : Splay
    
    def __contains__(self, item) -> bool:
        return item in self.cards

    def __len__(self) -> int:
        return len(self.cards)
    
    def top(self) -> Card:
        return self.cards[-1]
    
    def bottom(self) -> Card:
        return self.cards[0]

    def count_icon(self, targ_icon : Icon) -> int:
        # FIXME this is broken probably
        total : int = 0
        for card_no, card in enumerate(self.cards):
            if card_no == len(self.cards)-1:
                total += card.icons.count(targ_icon)
            else:
                total += len([card.icons[i] for i in splay_indices[self.splay] if card.icons[i] is targ_icon]) 
        return total
    

def get_empty_PlayerState() -> PlayerState:
    return PlayerState(
        hand=[],
        scored_cards=[],
        achieved_cards=[],
        special_achievements=[],
        board=get_empty_board()
    )


def get_empty_board() -> Dict[Color, Pile]:
    return {color: Pile(deque(), Splay.NONE) for color in Color}


# A PlayerState is a full-detail snapshot of a player's hand/board/etc.
@dataclass
class PlayerState:
    hand : List[Card]
    scored_cards : List[Card]
    achieved_cards : List[Card]
    special_achievements : List[SpecialAchievement]
    board : Dict[Color, Pile]

    def count_achievements(self) -> int:
        return len(self.achieved_cards)
    
    def count_score(self) -> int:
        return sum(card.age for card in self.scored_cards)
    
    def get_score_profile(self) -> Counter[int]:
        return Counter([card.age for card in self.scored_cards])
    
    def count_icon(self, targ_icon : Icon) -> int:
        return sum(pile.count_icon(targ_icon) for pile in self.board.values())
    
    def get_top_cards(self) -> List[Card]:
        out = []
        for color in Color:
            if len(self.board[color]) > 0:
                out.append(self.board[color].top())
        return out



@dataclass
class GameState:
    players : List[PlayerState]
    decks : List[Deque[Card]]  # NOTE that this does not extend to expansion draw rules!
    achievements : List[Card]
    special_achievements : List[SpecialAchievement]
    winner : Optional[int]
    debug : DebugHandler


GameStateTransition = Callable[[GameState], GameState]


# util function to sort a list of cards into appropriate decks.
# TODO: where should this go? maybe not this file...
def build_decks(all_cards : List[Card]) -> List[Deque[Card]]:
    decks = [[] for _ in range(11)]  # the 0 deck should always be empty
    for card in all_cards:
        decks[card.age].append(card)
    return decks