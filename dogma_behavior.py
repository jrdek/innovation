from dataclasses import dataclass
from game_state import Icon
from typing import List
from collections.abc import Callable
from lark import ParseTree
# TODO: consider using FrozenSets, FrozenLists, etc...


# DogmaActions are basically trees in our IR (corresponding to `stmt`s).
# Executing them is interpreting them (giving us a function GameState -> GameState),
# then applying the resulting function.
# see design notes for why we did it this way
# (TODO, maybe move that thoughtdump to here? decide later)

# also FIXME: these are a refined type from ParseTree... but I don't see a clean way
# to make refinement types in Python
DogmaAction = ParseTree


# A DEffect corresponds to `dogma_effect` in the grammar:
# - the `effect_header` is stored as DEffect.key_icon and DEffect.is_demand
# - the `stmts` are stored as a list of DogmaActions
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
            s += f"    {action}\n"  # TODO: better printing, probably with .pretty()
        return s
    

Dogma = List[DEffect]  # TODO: should I use this or not? how about other spots in the code?


# a dogma is what's executed by a "dogma" play in the game
# i.e., it may be multiple boxes on the card!
def parse_dogma(dogma_tree : ParseTree) -> Dogma:
    dogma : Dogma = []
    dogma_effects = dogma_tree.children
    for de in dogma_effects:
        header = de.children[0]
        stmts = de.children[1].children
        dclass = header.children[0]
        icon = Icon[header.children[1].children[0].upper()]
        is_demand = (dclass == "Demand")
        new_effect = DEffect(icon, stmts, is_demand)
        dogma.append(new_effect)
    return dogma