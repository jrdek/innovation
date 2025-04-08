"""
This file reads .cards files and turns them into Card objects.
Cards for baseline Innovation are described in `base_game.cards`.

Very ambitiously, my goal is to describe cards in a human-readable way.
This is broadly inspired by languages like Inform 7.
"""
from typing import List
from lark import Lark, Transformer
from structs import Color, Icon, Card
from dogma_ir import DogmaTransformer
import os

def clear_terminal():
    os.system('clear||cls')


# TODO: compartmentalize the dead-code checking
from utils.lark_utils import find_unused_rules


def get_cards_from_path(path : str) -> List[Card]:
    with open(path) as f:
        cards_txt = f.read()
    parser = Lark.open("grammars/deffect_grammar.lark", start="cards")
    syntax_tree = parser.parse(cards_txt)
    # TODO: enable this via flag
    #print(f'Unused rules: {find_unused_rules(tree, ("grammars/common", "grammars/deffect_grammar"))}')
    #input("(press any key...)")

    # TODO: IR conversion probably shouldn't go here, but maybe it's ok?
    # re-evaluate later
    ir_maker = DogmaTransformer()
    cards_in_ir : List[Card] = []
    clear_terminal()
    for i, card in enumerate(syntax_tree.children):
        #print(card.pretty())
        #print("-----\n")
        new_card = ir_maker.transform(card)
        # print(new_card.detailed_str())
        # input(f'(Cards shown: {i+1}/{len(syntax_tree.children)})')
        clear_terminal()
        cards_in_ir.append(new_card)

    #for card in cards_in_ir:
        #print(card.detailed_str())
    print(f"Loaded {len(cards_in_ir)} cards.")
    #input("(press any key...)")
    return cards_in_ir
