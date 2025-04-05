from __future__ import annotations 
from dataclasses import dataclass
from typing import List, Set, Dict, Deque, Callable, Optional
from collections import Counter, deque
from debug_handler import DFlags, DebugHandler
from structs import *
import random

from dogma_behavior import DEffect

# let's print out cards in their colors :)
card_colors : Dict[Color, str] = {
    Color.RED: '\033[91m',
    Color.YELLOW: '\033[93m',
    Color.GREEN: '\033[92m',
    Color.BLUE: '\033[94m',
    Color.PURPLE: '\033[95m'
}

color_end = '\033[0m'

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
    
    def __str__(self) -> str:
        return f"<{card_colors[self.color]}{self.name}{color_end}>"


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

    def __getitem__(self, idx) -> Card:
        return self.cards[idx]
    
    def __contains__(self, item) -> bool:
        return item in self.cards

    def __len__(self) -> int:
        return len(self.cards)

    def count_icon(self, targ_icon : Icon) -> int:
        total : int = 0
        for card in self[1:]:
            total += len([card.icons[i] for i in splay_indices[self.splay] if card.icons[i] is targ_icon])    


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
        return sum(pile.count_icons(targ_icon) for pile in self.board)


@dataclass
class GameState:
    players : List[PlayerState]
    decks : List[Deque[Card]]  # NOTE that this does not extend to expansion draw rules!
    achievements : List[Card]
    special_achievements : List[SpecialAchievement]
    winner : Optional[int]
    debug : DebugHandler
    

    # WARNING: this function breaks immutability of the class!
    # May be worth changing/reorganizing later. TODO.
    def setup_shuffle(self):
        random.shuffle(self.decks[-1])
        for deck in self.decks:
            random.shuffle(deck)
            #self.achievements.append(deck.pop())  # TODO: put elsewhere?


# util function to sort a list of cards into appropriate decks.
# TODO: where should this go? maybe not this file...
def build_decks(all_cards : List[Card]) -> List[Deque[Card]]:
    decks = [[] for _ in range(11)]  # the 0 deck should always be empty
    for card in all_cards:
        decks[card.age].append(card)
    return decks




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
    #             p.hand.add(drawn_card)
    #         p.agent.choose_meld_from_hand()


