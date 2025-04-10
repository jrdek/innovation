from enum import Enum, auto
from dataclasses import dataclass
from typing import Tuple

# It's nice to have debug flags not be arbitrary strings.
class DFlags(Enum):
    TURN_ACTION_CHOICES = auto()
    GAME_LOG = auto()

@dataclass
class DebugHandler:
    active_flags : Tuple[DFlags]
    
    # invoked as "if state.debug[MY_FLAG]: ..." -- a bit like a dict
    # TODO: is this a code smell? I think it looks elegant, but it's not
    # *that* readable...
    def __getitem__(self, item) -> bool:
        return item in self.active_flags


# TODO: consider making this a class decorator?
# it would be nice to have a `dprintf` function on a per-class basis