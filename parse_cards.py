"""
This file reads .techs files and turns them into Card objects.
Cards for baseline Innovation are described in `base_game.techs`.

Very ambitiously, my goal is to describe cards in a human-readable way.
This is broadly inspired by languages like Inform 7.
"""
from typing import List
from lark import Lark, Transformer
from game_state import Color, Icon
from game_state import Card
from dogma_behavior import DogmaAction, DEffect

from utils.lark_utils import find_unused_rules

# TODO: interpret!


def from_file(filename : str):  # todo typing
    with open(filename) as f:
        cards_txt = f.read()
    parser = Lark.open("grammars/deffect_grammar.lark", start="cards")
    tree = parser.parse(cards_txt)
    print(f'Unused rules: {find_unused_rules(tree, ("grammars/common", "grammars/deffect_grammar"), "cards")}')
    input("(press any key...)")
    return tree
    #return CardBuilder().transform(tree)
