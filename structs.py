from enum import Enum, auto


class Color(Enum):
    RED = auto()
    YELLOW = auto()
    GREEN = auto()
    BLUE = auto()
    PURPLE = auto()


class Icon(Enum):
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