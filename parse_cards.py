"""
This file reads .cards files and turns them into Card objects.
Cards for baseline Innovation are described in `base_game.cards`.

Very ambitiously, my goal is to describe cards in a human-readable way.
This is broadly inspired by languages like Inform 7.
"""
from typing import List
from lark import Lark, Transformer, ParseTree
from game_state import Color, Icon
from game_state import Card
from dogma_behavior import DogmaAction, DEffect, parse_dogma

# TODO: compartmentalize the dead-code checking
from utils.lark_utils import find_unused_rules


# this returns a tree of *all* the cards.
def get_cards_tree_from_path(path : str) -> ParseTree:
    with open(path) as f:
        cards_txt = f.read()
    parser = Lark.open("grammars/deffect_grammar.lark", start="cards")
    tree = parser.parse(cards_txt)
    # TODO: enable this via flag
    #print(f'Unused rules: {find_unused_rules(tree, ("grammars/common", "grammars/deffect_grammar"))}')
    #input("(press any key...)")


    print(tree.pretty())
    input("(press any key...)")
    return tree


def get_list_of_card_trees(allcards_tree : ParseTree) -> List[ParseTree]:
    assert allcards_tree.data == "cards"
    return allcards_tree.children


def get_card_trees_from_path(path : str) -> List[ParseTree]:
    return get_list_of_card_trees(get_cards_tree_from_path(path))


def get_cards_from_path(path : str) -> List[Card]:
    card_trees = get_card_trees_from_path(path)
    built_cards : List[Card] = []
    for tree in card_trees:
        # TODO: base_color isn't working right...
        card_name, card_age_raw, card_color_raw, card_icons_raw, card_dogma_raw = tree.children
        card_age : int = int(card_age_raw.children[0].children[0])
        card_color = Color.RED  # this parsing doesn't currently work! FIXME
        card_icons = card_icons_raw.children
        card_dogma : List[DogmaAction] = parse_dogma(card_dogma_raw)
        new_card : Card = Card(card_name, card_color, card_age, card_icons, card_dogma, faceup=False, owner=None)
        built_cards.append(new_card)
    return built_cards