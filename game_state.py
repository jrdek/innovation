from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Set, Dict, Deque
from collections import Counter, deque
import random

from dogma_behavior import DogmaFunc
from player_agents import PlayerAgent


class Color(Enum):
    RED = auto()
    YELLOW = auto()
    GREEN = auto()
    BLUE = auto()
    PURPLE = auto()


class Icon(Enum):
    GOLD = auto()
    PLANT = auto()
    LIGHT = auto()
    ROOK = auto()
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


@dataclass
class DEffect:
    effect : DogmaFunc
    is_demand : bool


@dataclass
class Card:
    name : str
    color : Color
    age : int
    icons : List[Icon]
    dogmata : List[DEffect]
    key_icon : Icon
    # Cards are hidden by default
    faceup : bool = False
    # Player IDs are represented as ints.
    # players[0] is None; all others are actual players
    owner : int = 0

    # card names are unique -- if two cards have the 
    # same name, then they are equal
    def __eq__(self, other):
        if type(other) is not Card: return False
        return self.name == other.name


@dataclass
class SpecialAchievement:
    name : str
    meets_cond : function
    # special achievements don't need to know who owns them


@dataclass
class Pile(deque):  # TODO is this how inheritance works
    splay : Splay = Splay.NONE
    
    def count_icon(self, targ_icon : Icon) -> int:
        total : int = 0
        for card in self[1:]:
            total += len([card.icons[i] for i in splay_indices[self.splay] if card.icons[i] is targ_icon])    


# A PlayerState is a full-detail snapshot of a player's hand/board/etc.
@dataclass
class PlayerState:
    hand : Set[Card]
    scored_cards : Set[Card]
    achieved_cards : Set[Card]
    special_achievements : Set[SpecialAchievement]
    board : Dict[Color, Pile]

    def __post_init__(self):
        self.board = {color: Pile() for color in Color}

    def count_achievements(self) -> int:
        return len(self.achieved_cards)
    
    def count_score(self) -> int:
        return sum(card.age for card in self.scored_cards)
    
    def get_score_profile(self) -> Counter[int]:
        return Counter([card.age for card in self.scored_cards])
    
    def count_icon(self, targ_icon : Icon) -> int:
        return sum(pile.count_icons(targ_icon) for pile in self.board)


@dataclass
class GameState:
    players : List[PlayerState]
    decks : List[Deque[Card]]
    achievements : List[Card]
    special_achievements : List[SpecialAchievement]

    def __post_init__(self):
        # 1. populate special achievements (TODO)
        # 2. populate self.decks (TODO)
        # 3. shuffle the decks and populate the achievements pile
        random.shuffle(self.decks[-1])
        for d in self.decks[-2:0:-1]:
            random.shuffle(self.decks[d])
            self.achievements.append(self.decks[d].pop())
        # now await the agents' choices
        










# TODO: This is all stateful.
    # def __init__(self, config : GameConfig):
    #     self.players = config.num_players
    #     # import all cards (facedown by default) and put them in decks by ages 1-10
    #     # to make everyone's life easier, we're "1-indexing" -- the 0th deck is empty
    #     self.decks : List[List[Card]] = [[] for _ in range(num_decks+1)]
    #     # (TODO)
    #     # then shuffle each deck and populate the achievements stack
    #     random.shuffle(self.decks[num_decks])
    #     self.achievements = [].pop
    #     for d in self.decks[num_decks-1:0:-1]:
    #         random.shuffle(self.decks[d])
    #         self.achievements.append(self.decks[d].pop())
    #     # special achievements, like dogmas, are given functionality elsewhere
    #     self.special_achievements : List[SpecialAchievement] = []  # TODO
    #     # deal every player two 1s
    #     # they must choose one to meld and one to keep
    #     assert len(self.players) * 2 <= len(self.decks[1])
    #     for p in self.players:
    #         for _ in range(2):
    #             drawn_card = self.decks[1].pop()
    #             drawn_card.owner = p
    #             p.hand.add(drawn_card)
    #         p.agent.choose_meld_from_hand()


