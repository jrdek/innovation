from __future__ import annotations

from enum import Enum, auto
from typing import List, Dict
from dataclasses import dataclass


class StrEnum(Enum):
    def __str__(self):
        return self.name


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
