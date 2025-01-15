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


class CardBuilder(Transformer):

    # TODO: separate Transformer class for DogmaBuild-ing?

    def deffect_grammar__NUM(self, number):
        try:
            return int(number)
        except ValueError:
            if number in ('a', 'an'):
                return 1
            number_terms = ('zero', 'one', 'two', 'three', 'four')
            if number not in number_terms:
                raise ValueError(f"Couldn't parse number term {number}")
            return number_terms.index(number)

    def deffect_grammar__common__AGE_VAL(self, age_val): 
        return self.common__AGE_VAL(age_val)
    
    def common__AGE_VAL(self, age_val):
        if age_val == 'counter':
            return 'counter'
        if age_val == 'plus-one':
            return 'plus-one'
        return int(age_val)
    
    def deffect_grammar__effect_header(self, items):
        is_demand : bool = ('Shared', 'Demand').index(items[0]) == 1
        key_icon : Icon = Icon[str(items[1]).upper()]
        return (is_demand, key_icon)
    
    def deffect_grammar__stmts(self, items):
        return tuple(items)
    
    def deffect_grammar__stmt(self, items):
        stmt = items[0]
        args = tuple(stmt.children)
        return DogmaAction(stmt.data[len('deffect_grammar__'):], args)
    
    def icons(self, items):
        return [Icon[str(i).upper()] for i in items]
    
    def dogma(self, items):  # list of DEffects
        return items
    
    def dogma_effect(self, items):  # one DEffect
        return DEffect(
            is_demand=items[0][0], key_icon=items[0][1], effects=items[1])

    def card(self, items):
        #card_name, age, color, icons, dogma = items
        card_name = str(items[0])
        age = items[1]
        color = Color[str(items[2]).upper()]
        icons = items[3]
        dogma = items[4]
        return Card(card_name, color, age, icons, dogma)    

    def cards(self, items): return items


def from_file(filename : str) -> List:
    with open(filename) as f:
        cards_txt = f.read()
    parser = Lark.open("card_grammar.lark", start="cards")
    tree = parser.parse(cards_txt)
    return CardBuilder().transform(tree)
