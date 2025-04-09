from lark import Transformer
# from enum import Enum, auto
# from collections.abc import Callable
from structs import Color, Icon, Splay, Dogma
from structs import Card, DEffect
from dogma_ir_typing import *
from typeguard import check_type
import dataclasses as dc
from typing import Tuple

"""
type system thoughts:

Many types are already defined elsewhere:
- nums are int instances
- cards are GameState.Card instances
- icons are Icon instances
- colors are Color instances

Everything else we need should be a base type (or something easily defined in `typing`)!
"""

# big important TODO:
# give all of the DogmaTransformer methods a return type annotation

class DogmaTransformer(Transformer):
    # COLOR LITERALS
    def common__red(self, _) -> Color:
        return Color.RED
    
    def common__yellow(self, _) -> Color:
        return Color.YELLOW
    
    def common__green(self, _) -> Color:
        return Color.GREEN
    
    def common__blue(self, _) -> Color:
        return Color.BLUE
    
    def common__purple(self, _) -> Color:
        return Color.PURPLE
    
    def base_color(self, children) -> ColorLiteralExpr:
        return ColorLiteralExpr(*children)
    
    def its_color(self, _) -> ColorOfCard:
        return ColorOfCard(ThoseOnesExpr())
    

    # DIRECTION LITERALS
    def dir_left(self, _) -> Splay:
        return Splay.LEFT
    
    def dir_right(self, _) -> Splay:
        return Splay.RIGHT
    
    def dir_up(self, _) -> Splay:
        return Splay.UP
    
    def direction(self, children) -> SplayDirection:
        return SplayDirection(*children)


    # ICON LITERALS
    def common__castle(self, _) -> Icon:
        return Icon.CASTLE
    
    def common__factory(self, _) -> Icon:
        return Icon.FACTORY

    def common__clock(self, _) -> Icon:
        return Icon.CLOCK

    def common__crown(self, _) -> Icon:
        return Icon.CROWN

    def common__leaf(self, _) -> Icon:
        return Icon.LEAF

    def common__idea(self, _) -> Icon:
        return Icon.IDEA

    def common__hex(self, _) -> Icon:
        return Icon.HEX

    def icon(self, children) -> IconLiteralExpr:
        return IconLiteralExpr(*children)


    # NUMBER LITERALS
    def common__zero(self, _) -> int:
        return 0
    
    def common__one(self, _) -> int:
        return 1
    
    def common__two(self, _) -> int:
        return 2
    
    def common__three(self, _) -> int:
        return 3
    
    def common__four(self, _) -> int:
        return 4
    
    def common__digits(self, children) -> int:
        return int(*children)

    def num(self, children) -> NumberLiteralExpr:
        return NumberLiteralExpr(*children)
    
    def its_value(self, _) -> ValueOfCard:
        return ValueOfCard(ThoseOnesExpr())

    def sum(self, children) -> SumExpr:
        return SumExpr(*children)
    
    def product(self, children) -> ProductExpr:
        return ProductExpr(*children)
    
    def round_down_quotient(self, children) -> QuotientExpr:
        return QuotientExpr(*children)
    
    def round_up_quotient(self, children) -> QuotientExpr:
        return QuotientExpr(*children, RoundedUp())

    
    def value_str(self, _) -> CardFeature:
        return NumbersExpr
    
    def color_str(self, _) -> CardFeature:
        return ColorsExpr
    
    def feature_of_cards(self, children) -> CardFeature:
        # FIXME: there's something hairy here
        # but it may not come up in the decks we have
        feature_kind, cards = children
        assert isinstance(cards, CardsThatExpr)
        if feature_kind is NumbersExpr:
            return ValuesOfCards(cards)
        else:
            assert feature_kind is ColorsExpr
            return ColorsOfCards(cards)
    
    def cards_feature(self, children) -> CardFeature:
        # <card>'s <feature>
        # (this is just feature_of_cards with the children reversed)
        return self.feature_of_cards(reversed(children))

    def choose_up_to_value(self, children) -> ChooseUpToNumberExpr:
        return ChooseUpToNumberExpr(*children)
    

    def card_name(self, children) -> CardNameExpr:
        return CardNameExpr(*children)


    def it(self, _) -> ReferentExpr:
        return ThoseOnesExpr()
    
    def them(self, _) -> ReferentExpr:
        return ThoseOnesExpr()


    def hand(self, _) -> AbstractZoneLiteral:
        return AbstractZoneLiteral(structs.PlayerField.HAND)
    
    def score_pile(self, _) -> AbstractZoneLiteral:
        return AbstractZoneLiteral(structs.PlayerField.SCORE_PILE)
    
    def achievements(self, _) -> AbstractZoneLiteral:
        return AbstractZoneLiteral(structs.PlayerField.ACHIEVEMENTS_PILE)
    
    def board(self, _) -> AbstractZoneLiteral:
        return AbstractZoneLiteral(structs.PlayerField.BOARD)
    
    # TODO: this is unsatisfying
    def top_cards(self, _) -> AbstractZoneLiteral:
        return TopCardsZone()
    

    def zone(self, children) -> PlayerZoneExpr:
        return PlayerZoneExpr(*children)

    def its(self, _) -> ReferentExpr:
        return ThoseOnesExpr()

    # wipe out player adjectives -- players suffice
    def my(self, _) -> PlayerExpr:
        return MeExpr()

    def you(self, _) -> PlayerExpr:
        return YouExpr()
    
    def your(self, _) -> PlayerExpr:
        return YouExpr()
    
    def their(self, _) -> PlayerExpr:
        return ThemExpr()
    
    def everyone(self, _) -> PlayerExpr:
        return EveryoneExpr()
    
    def everyones(self, _) -> PlayerExpr:
        return EveryoneExpr()
    
    def everyone_elses(self, _) -> PlayerExpr:
        return EveryoneElseExpr()
    
    def anyone(self, _) -> PlayerExpr:
        return AnyoneExpr()
    
    def anyones(self, _) -> PlayerExpr:
        return AnyoneExpr()
    
    def anyone_elses(self, _) -> PlayerExpr:
        return AnyoneElseExpr()
    
    def someone_else(self, _) -> PlayerExpr:
        return ChooseSomeoneExpr()
    
    def someone_elses(self, _) -> PlayerExpr:
        return ChooseSomeoneExpr()
    
    def someone(self, _) -> PlayerExpr:
        return ChooseSomeoneExpr()
    
    def someones(self, _) -> PlayerExpr:
        return ChooseSomeoneExpr()
    


    def below(self, _) -> NumericCompareOp:
        return BelowCompareOp()
    
    def at_least(self, _) -> NumericCompareOp:
        return AtLeastCompareOp()
    
    def equal_to(self, _) -> NumericCompareOp:
        return EqualToCompareOp()
    

    def comparison(self, children) -> ComparisonExpr:
        # TODO: typecheck here to account for "color [is] color"
        return ComparisonExpr(*children)
    
    
    def count(self, children) -> CountExpr:
        return CountExpr(*children)


    def any_quant(self, _) -> Quantifier:
        return AnyQuantifier()
    
    def all_quant(self, _) -> Quantifier:
        return AllQuantifier()
    
    def none_quant(self, _) -> Quantifier:
        return NoneQuantifier()


    def cards_have_icon(self, children) -> CardsAreLikeExpr:
        if len(children) == 3:
            quantifier, cards, icon = children
        else:
            assert(len(children) == 2)
            quantifier = AnyQuantifier()
            cards, icon = children
        like = HasFeatureFunc[Icon](icon)
        return CardsAreLikeExpr(cards=cards, like=like, quantifier=quantifier)
    
    def cond_and_cond(self, children) -> BoolExpr:
        return AndExpr(*children)
    
    def cond_or_cond(self, children) -> BoolExpr:
        return OrExpr(*children)
    
    def not_cond(self, children) -> BoolExpr:
        return NotExpr(*children)
    
    def you_do(self, _) -> BoolExpr:
        return SuccessExpr()
    
    def only_you_have_all_colors(self, _) -> BoolExpr:
        return OnlyYouHaveAllColorsExpr()

    def top(self, _) -> PileLoc:
        return TopOfPile()
    
    def bottom(self, _) -> PileLoc:
        return BottomOfPile()
    

    def card_at_loc_on_its_pile(self, children) -> FeaturesLike:
        pile_loc, other_restrictions = children
        return AndFunc[CardFeature](
            HasFeatureFunc[PileLoc](pile_loc),
            other_restrictions
        )
    
    def card_not_at_loc_on_its_pile(self, children) -> FeaturesLike:
        pile_loc, other_restrictions = children
        return AndFunc[CardFeature](
            NotFunc[PileLoc](HasFeatureFunc[PileLoc](pile_loc)),
            other_restrictions
        )
    
    def card_of_certain_age(self, children) -> FeaturesLike:
        return HasFeatureFunc[NumberExpr](children[0])
    
    def card_of_certain_color(self, children) -> FeaturesLike:
        color, other_restrictions = children
        return AndFunc[CardFeature](
            HasFeatureFunc[ColorExpr](color),
            other_restrictions
        )
    
    def card_with_certain_icon(self, children) -> FeaturesLike:
        other_restrictions, icon = children
        return AndFunc[CardFeature](
            other_restrictions,
            HasFeatureFunc[IconExpr](icon)
        )
    
    def card_not_of_certain_color(self, children) -> FeaturesLike:
        color, other_restrictions = children
        return AndFunc[CardFeature](
            NotFunc[ColorExpr](HasFeatureFunc[ColorExpr](color)),
            other_restrictions
        )
    
    def card_without_certain_icon(self, children) -> FeaturesLike:
        other_restrictions, icon = children
        return AndFunc[CardFeature](
            other_restrictions,
            NotFunc[IconExpr](HasFeatureFunc[IconExpr](icon))
        )

    def card_without_certain_name(self, children) -> FeaturesLike:
        other_restrictions, name = children
        return AndFunc[CardFeature](
            other_restrictions,
            NotFunc[CardNameExpr](HasFeatureFunc[CardNameExpr](name))
        )


    # TODO: do I still need this type in the parse tree?
    def kind_of_card(self, children) -> FeaturesLike:
        if not children:
            return AnyFeatures()  # fully permissive
        # otherwise, the children capture everything
        assert len(children) == 1
        return children[0]

    
    def players_color_cards(self, children) -> PlayersFeatureExpr[ColorExpr]:
        return PlayersFeatureExpr[ColorExpr](*children)
    
    
    # FIXME: This grammar rule should only ever describe card Color.
    # But it uses _feature_of_card to save on code duplication.
    # Rework the parse grammar to actually adhere to the constraint.

    # specifically, this rule is only ever used for splay stmts...
    # is this a grammar feature? i think yes!
    # (TODO: consider further)
    def players_cards_of_feature(self, children) -> PlayersFeatureExpr:
        player, feature = children
        if isinstance(feature, ColorsExpr):
            typing = ColorsExpr
        elif isinstance(feature, NumbersExpr):
            typing = NumbersExpr
        else:
            raise TypeError(f"Unhandled type {type(feature)}")
        return PlayersFeatureExpr[typing](player, feature)
    

    def any_color_of_player_cards(self, children) -> PlayersFeatureExpr[ColorExpr]:
        any_color, player = children
        return PlayersFeatureExpr[ColorExpr](player, any_color)
    
    def any_already_splayed(self, children) -> AnySplayedColorExpr:
        _, player, direction = children
        return AnySplayedColorExpr(player, direction)
    
    def pile_is_splayed_in_direction(self, children) -> PileIsSplayedExpr:
        player_color, direction = children
        players = player_color.players
        color = player_color.feature
        assert isinstance(color, ColorsExpr)
        return PileIsSplayedExpr(players, color, direction)


    def highest(self, _) -> Superlative:
        return HighestSuperlative()
    
    def lowest(self, _) -> Superlative:
        return LowestSuperlative()

    def sel_num_cards(self, children) -> ZonelessSelectionStrategy:
        num, superlative = NumberLiteralExpr(1), AnySelection()
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
    
    def sel_all_but_num_cards(self, children) -> ZonelessSelectionStrategy:
        return ZonelessSelectionStrategy(num=AllButNumberExpr(children[0]))
    
    def sel_all_cards(self, children) -> ZonelessSelectionStrategy:
        superlative = AnySelection()
        if children:
            assert len(children) == 1
            assert isinstance(children[0], Superlative)
            superlative = children[0]
        return ZonelessSelectionStrategy(selection_lambda=superlative)
    
    def card_sel_lambda(self, children) -> ZonelessSelectionStrategy:
        child = children[0]
        if isinstance(child, NumberExpr):
            return ZonelessSelectionStrategy(num=child)
        # otherwise, we built the strategy already
        return child
    
    # e.g., "highest top card"
    def selected_cards_from_some_pile(self, children) -> ZonelessCardsThatExpr:
        strat, that = children
        return ZonelessCardsThatExpr(that=that, strat=strat)
    
    def the_card_at_loc_on_its_pile(self, children) -> ZonelessCardsThatExpr:
        that = children[0]
        strat = ZonelessSelectionStrategy()
        return ZonelessCardsThatExpr(that=that, strat=strat)
    
    # TODO: think about coalescing the above with the below...
    # the type system makes this a little hairy

    def selected_cards_general(self, children) -> ZonelessCardsThatExpr:
        return self.selected_cards_from_some_pile(children)
    
    def selected_cards_conditioned(self, children) -> ZonelessCardsThatExpr:
        cards_that, condition = children
        cards_that.condition = condition
        return cards_that
    
    def selected_cards_from_player_pile(self, children) -> CardsThatExpr:
        player, zoneless_cards_that = children
        incomplete_strat = zoneless_cards_that.strat
        zone = PlayerZoneExpr(player, AbstractZoneLiteral(structs.PlayerField.BOARD))
        complete_strat = ZonedSelectionStrategy(
            src=zone,
            num=incomplete_strat.num,
            selection_lambda=incomplete_strat.selection_lambda
        )
        cards_that = CardsThatExpr(
            that=zoneless_cards_that.that,
            strat=complete_strat,
            condition=zoneless_cards_that.condition
        )
        return cards_that
    
    def selected_cards_from_player_zone(self, children) -> CardsThatExpr:
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
    
    def specific_cards(self, children) -> CardsExpr:
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

    def any_number_of(self, _) -> NumberExpr:
        return AnyNumber()
    
    def any_color(self, _) -> ColorExpr:
        return AnyColor()
    
    def color_or_color(self, children) -> ListOfColorsExpr:
        return ListOfColorsExpr(children)
    
    # NOTE that this is future-friendly
    def one_color_of_cards_on_board(self, children) -> ColorsOnPlayerBoardExpr:
        player = children[0]
        return ColorsOnPlayerBoardExpr(player)
    
    def any_value(self, _) -> NumberExpr:
        return AnyNumber()


    def cards_in_zone(self, children) -> CardsThatExpr:
        kind, zone = children
        strat = ZonedSelectionStrategy(src=zone)
        return CardsThatExpr(that=kind, strat=strat)
    
    def icons_in_zone(self, children) -> IconsInCardsExpr:
        icon, zone = children
        strat = ZonedSelectionStrategy(src=zone)
        cards = CardsThatExpr(that=AnyFeatures(), strat=strat)
        return IconsInCardsExpr(icons=icon, cards=cards)
    
    def icons_among_cards(self, children) -> IconsInCardsExpr:
        icon, cards = children
        return IconsInCardsExpr(icons=icon, cards=cards)
    
    def colors_on_only_your_board(self, _) -> ColorsExpr:
        return ColorsOnOnlyYourBoardExpr()

    def anyone(self, _) -> PlayerExpr:
        return AnyoneExpr
    
    def anyones(self, _) -> PlayerExpr:
        return AnyoneExpr
    
    def anyone_elses(self, _) -> PlayerExpr:
        return AnyoneElseExpr
    
    def nobody(self, _) -> PlayerExpr:
        return NobodyExpr()
    
    def everyone(self, _) -> PlayersExpr:
        return EveryoneExpr()
    
    def everyones(self, _) -> PlayersExpr:
        return EveryoneExpr()
    
    def everyone_elses(self, _) -> PlayersExpr:
        return EveryoneElseExpr()

    def demand_had_an_effect(self, _) -> DemandHadEffectExpr:
        return DemandHadEffectExpr(True)
    
    def demand_had_no_effect(self, _) -> DemandHadEffectExpr:
        return DemandHadEffectExpr(False)

    def cards_are_color(self, children) -> CardsAreLikeExpr:
        quantifier = AllQuantifier()
        if len(children) == 3:
            quantifier, cards, color_expr = children
        else:
            cards, color_expr = children
        color_feature = HasFeatureFunc(color_expr)
        return CardsAreLikeExpr(cards, color_feature, quantifier)
    
    def democracy_record(self, _) -> NumberExpr:
        return DemocracyRecordExpr()
    
    def player_score(self, children) -> PlayerScoreExpr:
        player, _ = children
        return PlayerScoreExpr(player)
    
    def chosen(self, _) -> ReferentExpr:
        return ChosenOnesExpr()
    
    def extreme_value(self, children) -> ExtremeValueExpr:
        return ExtremeValueExpr(*children)


    def meld_str(self, _) -> DrawAndFriendlyStmtName:
        return DrawAndFriendlyStmtName.MELD
    
    def reveal_str(self, _) -> DrawAndFriendlyStmtName:
        return DrawAndFriendlyStmtName.REVEAL
    
    def score_str(self, _) -> DrawAndFriendlyStmtName:
        return DrawAndFriendlyStmtName.SCORE
    
    def tuck_str(self, _) -> DrawAndFriendlyStmtName:
        return DrawAndFriendlyStmtName.TUCK


    def draw_stmt(self, children) -> DrawStmt:
        return DrawStmt(*children)

    def meld_stmt(self, children) -> MeldStmt:
        return MeldStmt(*children)
    
    def reveal_stmt(self, children) -> RevealStmt:
        return RevealStmt(*children)
    
    def score_stmt(self, children) -> ScoreStmt:
        return ScoreStmt(*children)
    
    def tuck_stmt(self, children) -> TuckStmt:
        return TuckStmt(*children)
    
    def draw_and_stmt(self, children) -> DrawAndStmt:
        then, amount, age = children
        return DrawAndStmt(amount, age, then)
    
    def for_every_countable(self, children) -> Tuple[CountableExpr, NumberLiteralExpr]:
        return (children[0], NumberLiteralExpr(1))
    
    def for_every_n_countables(self, children) -> Tuple[CountableExpr, NumberLiteralExpr]:
        return (children[1], children[0])
    
    def forward_for_stmt(self, children):
        countable_num_tuple, do_block = children
        countable, count_by = countable_num_tuple
        return ForStmt(countable, count_by, do_block)
    
    def backward_for_stmt(self, children):
        return self.forward_for_stmt(reversed(children))

    def if_stmt_without_else(self, children) -> IfStmt:
        return IfStmt(*children)
    
    def backwards_if_without_else(self, children) -> IfStmt:
        return IfStmt(children[1], children[0])
    
    def if_stmt_with_else(self, children) -> IfElseStmt:
        return IfElseStmt(*children)

    def repeat_stmt(self, _) -> RepeatStmt:
        return RepeatStmt()
    
    def return_stmt(self, children) -> ReturnStmt:
        return ReturnStmt(*children)

    def do_x_or_y_stmt(self, children) -> DoXOrYStmt:
        return DoXOrYStmt(*children)
    
    def you_may_stmt(self, children) -> YouMayStmt:
        return YouMayStmt(*children)
    
    def transfer_stmt(self, children) -> TransferStmt:
        return TransferStmt(*children)

    
    def splay_stmt(self, children) -> SplayStmt:
        playercolor = children[0]
        direction = SplayDirection(Splay.NONE)
        if len(children) == 2:
            direction = children[1]
        check_type(playercolor.feature, ColorsExpr)
        return SplayStmt(playercolor.players, playercolor.feature, direction)
    
    def special_achieve_stmt(self, children) -> SpecialAchieveStmt:
        name = children[0]
        return SpecialAchieveStmt(name)
    
    def nuke_stmt(self, children) -> NukeStmt:
        return NukeStmt(*children)
    
    def end_dogma_action_stmt(self, _) -> EndDogmaActionStmt:
        return EndDogmaActionStmt()
    
    def dogma_combo_stmt(self, children) -> DogmaComboStmt:
        return DogmaComboStmt(*children)
    

    def win_stmt(self, children) -> WinStmt:
        return WinStmt(*children)

    
    def nonpunc_grammatical_stmts(self, children) -> Stmts:
        return Stmts(children)
    
    def demand_stmts(self, children) -> Stmts:
        return Stmts(children)
    
    def shared_stmts(self, children) -> Stmts:
        return Stmts(children)



    # STUFF THAT'S ONLY USED BY CARDS, NOT DOGMAS

    # def dogma_effect(self, children) -> DEffect:
    #     effect_class, icon_expr, logic = children
    #     is_demand = (effect_class == "Demand")
    #     return DEffect(is_demand, icon_expr.icon, logic)

    def demand_dogma_effect(self, children) -> DEffect:
        icon_expr, logic = children
        return DEffect(is_demand=True, key_icon=icon_expr.icon, effects=logic)
    
    def shared_dogma_effect(self, children) -> DEffect:
        icon_expr, logic = children
        return DEffect(is_demand=False, key_icon=icon_expr.icon, effects=logic)

    def dogma(self, children) -> Dogma:
        return children

    def icons(self, children) -> List[Icon]:
        # since this is only ever used in defining cards,
        # we'll cut out the middleman (type)
        return [child.icon for child in children]

    def card(self, children) -> Card:  # CHECKME: this is returning a Card, *NOT* a CardExpr!
        name_block, number_block, color_block, icons, dogma = children
        name = name_block.name
        number = number_block.number
        color = color_block.color
        return Card(name, color, number, icons, dogma)
    
    def cards(self, children) -> List[Card]:
        return children
