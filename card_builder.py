from typing import List, Deque
from lark import Lark, Transformer
from structs import *
from dogma_ir import DogmaTransformer
from utils.lark_utils import find_unused_rules
import os

def clear_terminal():
    os.system('clear||cls')


"""
The CardStore has a few responsibilities:
- On initialization, parse and build IR trees for every card in the specified file.
- Expose an interface for games to access cards.
(Eventually, it would be nice to more concretely make this a lookup table; this way
GameStates can store IDs instead of full cards.)
"""
class CardStore:
    def __init__(self, paths: List[str]):
        self.paths = paths
        self.cards : List[Card] = []
        for path in self.paths:
            self.populate_cards(path)


    def populate_cards(self, path: str):
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
        self.cards += cards_in_ir







