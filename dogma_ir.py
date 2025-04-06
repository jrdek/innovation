from lark import Transformer
# from enum import Enum, auto
# from collections.abc import Callable
from structs import Color, Icon, Splay
from structs import Card, DEffect
from dogma_ir_typing import *
from typeguard import check_type
import dataclasses as dc


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
    
    def its_color(self, _):
        return ColorOfCard(ThoseOnesExpr())
    

    # DIRECTION LITERALS
    def dir_left(self, _):
        return Splay.LEFT
    
    def dir_right(self, _):
        return Splay.RIGHT
    
    def dir_up(self, _):
        return Splay.UP
    
    def direction(self, children):
        return SplayDirection(*children)


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
    
    def its_value(self, children):
        return ValueOfCard(ThoseOnesExpr())
    

    def sum(self, children):
        return SumExpr(*children)
    
    def product(self, children):
        return ProductExpr(*children)
    
    def round_down_quotient(self, children):
        return QuotientExpr(*children)
    
    def round_up_quotient(self, children):
        return QuotientExpr(*children, RoundedUp())

    
    def value_str(self, _):
        return NumbersExpr
    
    def color_str(self, _):
        return ColorsExpr
    
    def feature_of_cards(self, children):
        # FIXME: there's something hairy here
        # but it may not come up in the decks we have
        feature_kind, cards = children
        assert isinstance(cards, CardsThatExpr)
        if feature_kind is NumbersExpr:
            return ValuesOfCards(cards)
        else:
            assert feature_kind is ColorsExpr
            return ColorsOfCards(cards)
    
    def cards_feature(self, children):
        return self.feature_of_cards([children[1], children[0]])


    def up_to_value(self, children):
        return UpToNumberExpr(*children)
    

    def card_name(self, children):
        return CardNameExpr(*children)


    def it(self, _):
        return ThoseOnesExpr()
    
    def them(self, _):
        return ThoseOnesExpr()


    def hand(self, _):
        return AbstractZoneLiteral(structs.PlayerField.HAND)
    
    def score_pile(self, _):
        return AbstractZoneLiteral(structs.PlayerField.SCORE_PILE)
    
    def achievements(self, _):
        return AbstractZoneLiteral(structs.PlayerField.ACHIEVEMENTS_PILE)
    
    def board(self, _):
        return AbstractZoneLiteral(structs.PlayerField.BOARD)
    
    def top_cards(self, _):
        return TopCardsZone()
    

    def zone(self, children):
        return PlayerZoneExpr(*children)

    def you(self, _):
        return YouExpr()
    
    def your(self, _):
        return YouExpr()
    
    def my(self, _):
        return MeExpr()
    
    def anyone_elses(self, _):
        return AnyoneElseExpr()

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
            quantifier = AnyQuantifier()
            cards, icon = children
        like = HasFeatureFunc[Icon](icon)
        return CardsAreLikeExpr(cards=cards, like=like, quantifier=quantifier)
    
    def cond_and_cond(self, children):
        return AndExpr(*children)
    
    def cond_or_cond(self, children):
        return OrExpr(*children)
    
    def not_cond(self, children):
        return NotExpr(*children)
    
    def you_do(self, _):
        return SuccessExpr()

    def top(self, _):
        return TopOfPile()
    
    def bottom(self, _):
        return BottomOfPile()
    
    def card_at_loc_on_its_pile(self, children):
        pile_loc, other_restrictions = children
        return AndFunc[CardFeature](
            HasFeatureFunc[PileLoc](pile_loc),
            other_restrictions
        )
    
    def card_not_at_loc_on_its_pile(self, children):
        pile_loc, other_restrictions = children
        return AndFunc[CardFeature](
            NotFunc[PileLoc](HasFeatureFunc[PileLoc](pile_loc)),
            other_restrictions
        )
    
    def card_of_certain_age(self, children):
        return HasFeatureFunc[NumberExpr](children[0])
    
    def card_of_certain_color(self, children):
        color, other_restrictions = children
        return AndFunc[CardFeature](
            HasFeatureFunc[ColorExpr](color),
            other_restrictions
        )
    
    def card_with_certain_icon(self, children):
        other_restrictions, icon = children
        return AndFunc[CardFeature](
            other_restrictions,
            HasFeatureFunc[IconExpr](icon)
        )
    
    def card_not_of_certain_color(self, children):
        color, other_restrictions = children
        return AndFunc[CardFeature](
            NotFunc[ColorExpr](HasFeatureFunc[ColorExpr](color)),
            other_restrictions
        )
    
    def card_without_certain_icon(self, children):
        other_restrictions, icon = children
        return AndFunc[CardFeature](
            other_restrictions,
            NotFunc[IconExpr](BoolFunc[IconExpr](icon))
        )

    def card_without_certain_name(self, children):
        other_restrictions, name = children
        return AndFunc[CardFeature](
            other_restrictions,
            NotFunc[CardNameExpr](BoolFunc[CardNameExpr](name))
        )


    # TODO: do I still need this type in the parse tree?
    def kind_of_card(self, children):
        if not children:
            return AnyFeatures()  # fully permissive
        # otherwise, the children capture everything
        assert len(children) == 1
        return children[0]

    
    def players_color_cards(self, children):
        return PlayersFeatureExpr(*children)
    
    
    def players_cards_of_feature(self, children):
        player, feature = children
        if isinstance(feature, ColorsExpr):
            typing = ColorsExpr
        elif isinstance(feature, NumbersExpr):
            typing = NumbersExpr
        else:
            raise TypeError(f"Unhandled type {type(feature)}")
        return PlayersFeatureExpr[typing](player, feature)
    

    def any_color_of_player_cards(self, children):
        any_color, player = children
        return PlayersFeatureExpr[ColorExpr](player, any_color)
    
    def any_already_splayed(self, children):
        _, player, direction = children
        return AnySplayedColorExpr(player, direction)

    def highest(self, _):
        return HighestSuperlative()
    
    def lowest(self, _):
        return LowestSuperlative()

    def sel_num_cards(self, children):
        superlative, num = AnySelection(), 1
        if len(children) == 1:
            if isinstance(children[0], Superlative):
                superlative = children[0]
            else:
                assert isinstance(children[0], NumberLiteralExpr)
                num = children[0]
        elif len(children) > 1:
            assert len(children) == 2
            superlative, num = children
        return ZonelessSelectionStrategy(num=num, selection_lambda=superlative)
    
    def sel_all_cards(self, children):
        superlative = AnySelection()
        if children:
            assert len(children) == 1
            assert isinstance(children[0], Superlative)
            superlative = children[0]
        return ZonelessSelectionStrategy(selection_lambda=superlative)
    
    def card_sel_lambda(self, children):
        child = children[0]
        if isinstance(child, NumberExpr):
            return ZonelessSelectionStrategy(num=child)
        # otherwise, we built the strategy already
        return child
    
    def selected_cards_from_some_pile(self, children):
        strat, that = children
        return ZonelessCardsThatExpr(that=that, strat=strat)
    
    # TODO: think about coalescing the above with the below...

    def selected_cards_general(self, children):
        return self.selected_cards_from_some_pile(children)
    
    def selected_cards_conditioned(self, children):
        cards_that, condition = children
        cards_that.condition = condition
        return cards_that
    
    def selected_cards_from_player_pile(self, children):
        player, zoneless_cards_that = children
        incomplete_strat = zoneless_cards_that.strat
        zone = PlayerZoneExpr(player, AbstractZoneLiteral(structs.PlayerField.BOARD))
        complete_strat = ZonedSelectionStrategy(
            zone,
            incomplete_strat.num,
            incomplete_strat.selection_lambda
        )
        cards_that = CardsThatExpr(
            zoneless_cards_that.that,
            complete_strat,
            zoneless_cards_that.condition
        )
        return cards_that
    
    def selected_cards_from_player_zone(self, children):
        cards_that, zone = children
        return CardsThatExpr(
            that=cards_that.that,
            strat=ZonedSelectionStrategy(
                src=zone,
                num=cards_that.strat.num,
                selection_lambda=cards_that.strat.selection_lambda
            ),
            condition=cards_that.condition
        )
    
    def specific_cards(self, children):
        # TODO: cases :(
        if isinstance(children[0], ZonelessSelectionStrategy):
            strat = children[0]
            that = children[1]
            #assert isinstance(that, FeaturesLike)  <-- this fails because FeaturesLike is a
            # subscripted generic...
            check_type(that, FeaturesLike)
            # TODO: parse the remaining 2-3 args in the first two cases
            return CardsThatExpr(that=that, strat=strat)
        print(children[0])
        raise Exception(f"Unhandled type for children[0]: {type(children[0])}")

    def any_number_of(self, _):
        return AnyNumber()
    
    def any_color(self, _):
        return AnyColor()
    
    def any_value(self, _):
        return AnyNumber()


    def cards_in_zone(self, children):
        kind, zone = children
        strat = ZonedSelectionStrategy(src=zone)
        return CardsThatExpr(that=kind, strat=strat)
    
    def icons_in_zone(self, children):
        icon, zone = children
        strat = ZonedSelectionStrategy(src=zone)
        cards = CardsThatExpr(that=AnyFeatures(), strat=strat)
        return IconsInCardsExpr(icons=icon, cards=cards)
    
    def icons_among_cards(self, children):
        icon, cards = children
        return IconsInCardsExpr(icons=icon, cards=cards)
    
    def colors_on_only_your_board(self, _):
        return ColorsOnOnlyYourBoardExpr()

    def anyone(self, _):
        return AnyoneExpr
    
    def anyones(self, _):
        return AnyoneExpr
    
    def anyone_elses(self, _):
        return AnyoneElseExpr
    
    def nobody(self, _):
        return NobodyExpr()
    
    def everyone(self, _):
        return EveryoneExpr()
    
    def everyones(self, _):
        return EveryoneExpr()
    
    def everyone_elses(self, _):
        return EveryoneElseExpr()

    def any_cards_transferred(self, children):
        actor = children[0]
        return CardsWereTransferredExpr(actor)

    def cards_are_color(self, children):
        quantifier = AllQuantifier()
        if len(children) == 3:
            quantifier, cards, color_expr = children
        else:
            cards, color_expr = children
        color_feature = HasFeatureFunc(color_expr)
        return CardsAreLikeExpr(cards, color_feature, quantifier)
    
    def democracy_record(self, _):
        return DemocracyRecordExpr()
    
    def player_score(self, children):
        player, _ = children
        return player
    
    def chosen(self, _):
        return ChosenOnesExpr()
    
    def extreme_value(self, children):
        return ExtremeValueExpr(*children)


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
    
    def transfer_stmt(self, children):
        return TransferStmt(*children)
    
    def tuck_stmt(self, children):
        return TuckStmt(*children)
    
    def splay_stmt(self, children):
        playercolor = children[0]
        direction = SplayDirection(None)
        if len(children) == 2:
            direction = children[1]
        check_type(playercolor.feature, ColorsExpr)
        return SplayStmt(playercolor.players, playercolor.feature, direction)
    
    def special_achieve_stmt(self, children):
        name = children[0]
        return SpecialAchieveStmt(name)
    

    def stmts(self, children):
        return Stmts(children)



    # STUFF THAT'S ONLY USED BY CARDS, NOT DOGMAS

    def dogma_effect(self, children):
        effect_class, icon_expr, logic = children
        is_demand = (effect_class == "Demand")
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