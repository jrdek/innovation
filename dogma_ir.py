from lark import Transformer, ParseTree
# from enum import Enum, auto
# from collections.abc import Callable
from structs import Color, Icon
from structs import Card, DEffect
from dogma_ir_typing import *


"""
type system thoughts:

Many types are already defined elsewhere:
- nums are int instances
- cards are GameState.Card instances
- icons are Icon instances
- colors are Color instances

Everything else we need should be a base type (or something easily defined in `typing`)!
"""


class DogmaTransformer(Transformer):
    # COLOR LITERALS
    def common__red(self, _):
        return Color.RED
    
    def common__yellow(self, _):
        return Color.YELLOW
    
    def common__green(self, _):
        return Color.GREEN
    
    def common__blue(self, _):
        return Color.BLUE
    
    def common__purple(self, _):
        return Color.PURPLE
    
    def base_color(self, children):
        return ColorLiteralExpr(*children)
    

    # ICON LITERALS
    def common__castle(self, _):
        return Icon.CASTLE
    
    def common__factory(self, _):
        return Icon.FACTORY

    def common__clock(self, _):
        return Icon.CLOCK

    def common__crown(self, _):
        return Icon.CROWN

    def common__leaf(self, _):
        return Icon.LEAF

    def common__idea(self, _):
        return Icon.IDEA

    def common__hex(self, _):
        return Icon.HEX

    def icon(self, children):
        return IconLiteralExpr(*children)


    # NUMBER LITERALS
    def common__zero(self, _):
        return 0
    
    def common__one(self, _):
        return 1
    
    def common__two(self, _):
        return 2
    
    def common__three(self, _):
        return 3
    
    def common__four(self, _):
        return 4
    
    def common__digits(self, children):
        return int(*children)

    def num(self, children):
        return NumberLiteralExpr(*children)
    
    

    def up_to_value(self, children):
        return UpToNumberExpr(*children)
    

    def card_name(self, children):
        return CardNameExpr(*children)


    def it(self, _):
        return ThoseOnesExpr()
    
    def them(self, _):
        return ThoseOnesExpr()


    def hand(self, _):
        return HandZone()
    
    def score_pile(self, _):
        return ScoreZone()
    
    def achievements(self, _):
        return AchievementsZone()
    
    def board(self, _):
        return BoardZone()
    
    def top_cards(self, _):
        return TopCardsZone()
    

    def zone(self, children):
        return PlayerZoneExpr(*children)

    
    def your(self, _):
        return YouExpr()
    

    def below(self, _):
        return BelowCompareOp()
    
    def at_least(self, _):
        return AtLeastCompareOp()
    
    def compare_op(self, children):
        return children[0]
    

    def comparison(self, children):
        return ComparisonExpr(*children)
    
    
    def count(self, children):
        return CountExpr(*children)


    def any_quant(self, _):
        return AnyQuantifier()
    
    def all_quant(self, _):
        return AllQuantifier()


    def cards_have_icon(self, children):
        if len(children) == 3:
            quantifier, cards, icon = children
        else:
            assert(len(children) == 2)
            quantifier = None
            cards, icon = children
        like = FeaturesLike(has_icon=icon)
        return CardsAreLikeExpr(cards, like, quantifier)
        


    def kind_of_card(self, children):
        # TODO: probably room for some good disjunction/conjunction logic here...
        pile_loc, is_color, not_color, has_icon, without_icon = None, None, None, None, None
        in_zone = None
        for child in children:
            # TODO: copy-construct manually here, I think
            pass
        features = FeaturesLike(pile_loc, is_color, not_color, has_icon, without_icon, in_zone)
        return features
    

    def highest(self, _):
        return HighestSuperlative()
    
    def lowest(self, _):
        return LowestSuperlative()

    def sel_num_cards(self, children):
        superlative, num = None, None
        if len(children) == 1:
            if isinstance(children[0], Superlative):
                superlative = children[0]
            else:
                assert isinstance(children[0], NumberLiteralExpr)
                num = children[0]
        else:
            superlative, num = children
        return SelectionStrategy(num=num, selection_lambda=superlative)
    
    def sel_all_cards(self, children):
        superlative = None
        if children:
            assert len(children) == 1
            assert isinstance(children[0], Superlative)
            superlative = children[0]
        return SelectionStrategy(selection_lambda=superlative)
    
    def card_sel_lambda(self, children):
        child = children[0]
        if isinstance(child, NumberExpr):
            return SelectionStrategy(num=child)
        # otherwise, we built the strategy already
        return child
    
    def specific_cards(self, children):
        # TODO: cases :(
        if isinstance(children[0], SelectionStrategy):
            strat = children[0]
            that = children[1]
            assert type(that) is FeaturesLike
            # TODO: parse the remaining 2-3 args in the first two cases
            return CardsThatExpr(that=that, strat=strat)
        raise Exception(f"Unhandled type for children[0]: {type(children[0])}")




    def countable(self, children):
        # TODO: lots of case work
        if isinstance(children[0], FeaturesLike):
            assert len(children) == 2
            features, zone = children
            features.in_zone = zone
            return CardsThatExpr(that=features)
        raise Exception(f"Unhandled type for children[0]: {type(children[0])}")


    def draw_stmt(self, children):
        return DrawStmt(*children)
    
    def reveal_stmt(self, children):
        return RevealStmt(*children)

    def if_stmt(self, children):
        return IfStmt(*children)

    def repeat_stmt(self, _):
        return RepeatStmt()

    def score_stmt(self, children):
        return ScoreStmt(*children)
    
    def return_stmt(self, children):
        return ReturnStmt(*children)
    
    def meld_stmt(self, children):
        return MeldStmt(*children)
    
    def you_may_stmt(self, children):
        return YouMayStmt(*children)
    

    def stmts(self, children):
        return Stmts(children)



    # STUFF THAT'S ONLY USED BY CARDS, NOT DOGMAS

    def dogma_effect(self, children):
        is_demand, icon_expr, logic = children
        return DEffect(is_demand, icon_expr.icon, logic)
    
    def dogma(self, children):
        return children

    def icons(self, children):
        # since this is only ever used in defining cards,
        # we'll cut out the middleman (type)
        return [child.icon for child in children]

    def card(self, children):  # CHECKME: this is returning a Card, *NOT* a CardExpr!
        name_block, number_block, color_block, icons, dogma = children
        name = name_block.name
        number = number_block.number
        color = color_block.color
        return Card(name, color, number, icons, dogma)
    
    def cards(self, children):
        return children
