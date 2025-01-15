from dataclasses import dataclass
from game_state import Icon
from typing import List


@dataclass
class DogmaAction:
    name : str
    args : List  # (of any)


@dataclass
class DEffect:
    key_icon : Icon
    effects : List[DogmaAction]
    is_demand : bool

    def __str__(self):
        s = ''
        kind = "Demand" if self.is_demand else "Shared"
        s += f"- {kind} ({self.key_icon.name}):\n"
        for action in self.effects:
            s += f"    {action}\n"
        return s
