"""
I'm essentially writing a compiler:
    Input: Card definitions (expressed in an easily-parsed subset of English)
    Output: Functions which take a GameState and return a new GameState

A type system will be valuable here, especially because sometimes players
have to choose things of a given type!

The point of the IR is to translate our Lark tree into just everyday Python.
Instead of "tree nodes" having a .children list, they will have named fields.

Note that cards are immutable (and we probably won't ever want to mutate them).
"""

from abc import ABC, abstractmethod  # TODO: do I actually *need* ABCs here? i suspect not
from typing import List, Union, Optional, TypeVar, Generic, Tuple
from dataclasses import dataclass
from enum import Enum, auto
import structs
import lark
from collections.abc import Callable
from frozenlist import FrozenList
from structs import *


"""
TODO:
- Organize this file's definitions! They're scattered.
- (evaluate a few typing decisions)
"""


# If something is an instance of Choice, then the interpreter
# knows to ask the PlayerAgent to choose something.
class Choice:
    pass


class IRTreeNode:
    """
    FIXME: It would probably be cleaner here to parse these into JSON-like structs,
    then print them from that. This is starting to be slightly spaghetti. (It's just also
    not core-functionality code, so I'm not too stressed about that.)
    """

    """
    Pretty-print IRTreeNodes.
    Recursively, any children of a node which aren't successfully transformed into IRTreeNodes
    are printed in red to show that I still need to implement them.
    """
    def __str_helper__(self) -> List[Union[str, List]]:  # TODO: type better
        out_list = [type(self).__name__]
        for key, value in self.__dict__.items():
            if key == "__orig_class__":
                continue  # don't care about this for now - it's a Typing artifact
            elif isinstance(value, IRTreeNode):
                value_repr = value.__str_helper__()
            elif isinstance(value, lark.Tree):
                value_repr = structs.colored_str(value.pretty(), structs.Color.RED)
            else:
                value_repr = [str(value)]

            if len(value_repr) == 1 and isinstance(value_repr[0], str):
                new_item = [f"{key}={value_repr[0]}"] 
            else:
                new_item = (key, value_repr)
            out_list.append(new_item)
        return out_list


    def __str__(self):
        # handle indentation here
        INDENT = '  '
        outstr = ""
        recursed_list = self.__str_helper__()
        # input(recursed_list)
        child_stack = [recursed_list]  # stack of lists...
        index_stack = []  # and the indices we use to access them.
        index = 0
        while child_stack:
            indent_str = len(child_stack)*INDENT
            if index not in range(len(child_stack[-1])):
                child_stack.pop()
                if child_stack:
                    index = index_stack.pop() + 1
            else:
                here = child_stack[-1][index]
                if isinstance(here, str):
                    for line in here.split('\n'):
                        outstr += indent_str + f"{line}\n"
                    index += 1
                else:  
                    # descend (it's a list/tuple)
                    child_stack.append(here)
                    index_stack.append(index)
                    # FIXME: this tuple case is cursed but should work
                    if isinstance(here, tuple):
                        outstr += indent_str + "  " + here[0] + "=\n"
                        index = 1
                    else:
                        assert isinstance(here, list)
                        index = 0
        return outstr[:-1]


class Stmt(IRTreeNode):
    pass


# a Stmts object is the root of every DEffect tree
# TODO: pretty-printing Stmts objects is half broken
class Stmts(IRTreeNode, Tuple[Stmt]):  # TODO: This is breaking some or other idiom. Does this *have* a List, or *is* it a List?
    def __str_helper__(self):
        if not self:
            return ["[]"]
        return [stmt.__str_helper__() 
                if isinstance(stmt, Stmt) 
                else structs.colored_str(stmt.pretty(), structs.Color.RED) 
                for stmt in self]
    
    def pretty(self):
        return self.__str__

    def __str__(self):
        if len(self) == 0:
            return "[]"
        return '\n'.join(str(stmt) for stmt in self)
    
    def interp(self, di):
        return di.interp_stmts(self)


class Expr(IRTreeNode):
    pass


class CardFeature(Expr):
    pass


T = TypeVar(name="T")
F = TypeVar(name="F", bound=CardFeature)


class Quantifier(IRTreeNode):
    pass


class AnyQuantifier(Quantifier):
    def interp(self, di) -> Callable[[Tuple[T]], bool]:
        return di.interp_anyquantifier()


class NoneQuantifier(Quantifier):
    def interp(self, di) -> Callable[[Tuple[T]], bool]:
        return di.interp_nonequantifier()


class AllQuantifier(Quantifier):
    def interp(self, di) -> Callable[[Tuple[T]], bool]:
        return di.interp_allquantifier()


class CountableExpr(Expr):
    pass


class BoolExpr(Expr):
    pass


class SuccessExpr(BoolExpr):
    pass


class OnlyYouHaveAllColorsExpr(BoolExpr):
    pass


# type which maps Ts to bools; basically a predicate on Ts
class BoolFunc(IRTreeNode, Generic[T]):
    pass


FeaturesLike = BoolFunc[CardFeature]


class NumbersExpr(CountableExpr, CardFeature):
    pass


class NumberExpr(NumbersExpr):
    pass


class AllNumberExpr(NumberExpr):
    pass


@dataclass(frozen=True)
class AllButNumberExpr(NumberExpr):
    num: NumberExpr


class IconsExpr(CountableExpr, CardFeature):
    pass


class IconExpr(IconsExpr):
    pass


class ColorsExpr(CountableExpr, CardFeature):
    pass


class ColorExpr(ColorsExpr):
    pass


class PlayersExpr(CountableExpr):
    pass


class PlayerExpr(PlayersExpr):
    pass
    

class AbstractZone(IRTreeNode):
    pass


@dataclass(frozen=True)
class PlayerZoneExpr(Expr):
    player: PlayerExpr
    zone: AbstractZone

    def interp(self, di) -> Tuple[PlayerId, PlayerField]:
        return di.interp_playerzoneexpr(self)


class CardsExpr(CountableExpr):
    @abstractmethod
    def get_zones(self, di) -> Tuple[Tuple[PlayerId, PlayerField]]:
        ...


class CardExpr(CardsExpr):  # TODO: evaluate design re: these separate plural types
    pass


class ReferentExpr(CardExpr):
    # TODO: is this always a CardExpr?
    def get_zones(self, di) -> Tuple[Tuple[PlayerId, PlayerField]]:
        return di.get_referentexpr_zones()


class ThoseOnesExpr(ReferentExpr):
    def interp(self, di):
        return di.interp_thoseonesexpr()


class OtherOnesExpr(ReferentExpr):
    pass


class ChosenOnesExpr(ReferentExpr):
    pass


# FIXME: "their" is totally a referent, but only to players...
class ThemExpr(PlayerExpr):
    pass


class DemocracyRecordExpr(NumberExpr):
    pass


class PileLoc(CardFeature):
    pass


class BottomOfPile(PileLoc):
    pass


class TopOfPile(PileLoc):
    pass




class AnyFeatures(FeaturesLike):
    def interp(self, di) -> CardProp:
        return di.interp_anyfeatures()

class SelectionLambda(IRTreeNode):
    pass

class AnySelection(SelectionLambda):
    pass

class Superlative(SelectionLambda):
    pass

class HighestSuperlative(Superlative):
    pass

class LowestSuperlative(Superlative):
    def interp(self, di) -> Callable[[Tuple[T]], T]:
        return di.interp_lowestsuperlative()

@dataclass(frozen=True)
class ExtremeValueExpr(NumberExpr):
    superlative: Superlative
    zone: PlayerZoneExpr

class ColorsOnOnlyYourBoardExpr(ColorsExpr):
    pass

# How many of which cards are we selecting?
# (FIXME: kw_only is a hack to allow subclasses with non-default args)
@dataclass(frozen=True, kw_only=True)
class ZonelessSelectionStrategy(IRTreeNode):
    num: NumberExpr = AllNumberExpr()
    selection_lambda: SelectionLambda = AnySelection()

# From where?
@dataclass(frozen=True)
class ZonedSelectionStrategy(ZonelessSelectionStrategy):
    src: PlayerZoneExpr
    
    def interp(self, di) -> EvaluatedZonedSelectionStrategy:
        return di.interp_zonedselectionstrategy(self)





@dataclass(frozen=True)
class CardsAreLikeExpr(BoolExpr):
    cards: CardsExpr
    like: FeaturesLike
    quantifier: Optional[Quantifier] = AnyQuantifier()  # CHECKME: not all?
    
    def interp(self, di) -> bool:
        return di.interp_cardsarelikeexpr(self)


@dataclass(frozen=True)
class CountExpr(NumberExpr):
    countable: CountableExpr


class PointsExpr(NumberExpr):
    pass


@dataclass(frozen=True)
class NumberLiteralExpr(NumberExpr):
    number: int

    def interp(self, di) -> int:
        return di.interp_numberliteralexpr(self)


@dataclass(frozen=True)
class IconLiteralExpr(IconExpr):
    icon: structs.Icon

    def interp(self, di) -> Icon:
        return di.interp_iconliteralexpr(self)


@dataclass(frozen=True)
class ColorLiteralExpr(ColorExpr):
    color: structs.Color


@dataclass(frozen=True)
class ChooseUpToNumberExpr(NumberExpr, Choice):
    # user must choose how many, up to [num].
    upper_bound: NumberExpr


@dataclass(frozen=True)
class SumExpr(NumberExpr):
    left: NumberExpr
    right: NumberExpr


@dataclass(frozen=True)
class ProductExpr(NumberExpr):
    left: NumberExpr
    right: NumberExpr


class RoundDir(IRTreeNode):
    pass


class RoundedUp(RoundDir):
    pass


class RoundedDown(RoundDir):
    pass


@dataclass(frozen=True)
class QuotientExpr(NumberExpr):
    dividend: NumberExpr
    divisor: NumberExpr
    round_dir: RoundDir = RoundedDown()


@dataclass(frozen=True)
class PlayerScoreExpr(NumberExpr):
    player: PlayerExpr


class NoCondition(BoolExpr):
    def interp(self, di) -> bool:
        return di.interp_nocondition()


@dataclass(frozen=True)
class ZonelessCardsThatExpr(CardsExpr):
    that: FeaturesLike
    strat: Optional[ZonelessSelectionStrategy] = None  # TODO: de-Noneify this
    condition: BoolExpr = NoCondition()

    def get_zones(self, di) -> Tuple[Tuple[PlayerId, PlayerField]]:
        return di.get_zonelesscardsthatexpr_zones(self)


# TODO: should this inherit from ZonelessCardsThat?
@dataclass(frozen=True)
class CardsThatExpr(CardsExpr):
    that: FeaturesLike
    strat: Optional[ZonedSelectionStrategy] = None # TODO: what to do if this is None?
    condition: BoolExpr = NoCondition()

    def interp(self, di) -> Tuple[CardId]:
        return di.interp_cardsthatexpr(self)

    def get_zones(self, di) -> Tuple[Tuple[PlayerId, PlayerField]]:
        return di.get_cardsthatexpr_zones(self)
    

@dataclass(frozen=True)
class IconsInCardsExpr(NumberExpr):
    icons: IconsExpr
    cards: CardsThatExpr


class CardNamesExpr(CardExpr, CardFeature):  # CardExpr because you can refer to cards by their names
    def get_zones(self, di) -> Tuple[Tuple[PlayerId, PlayerField]]:
        # TODO: is this needed?
        raise Exception("Unimplemented")


@dataclass(frozen=True)
class CardNameExpr(CardNamesExpr):
    name: str

class NumericCompareOp(IRTreeNode):
    pass

class BelowCompareOp(NumericCompareOp):
    pass

class AtLeastCompareOp(NumericCompareOp):
    pass

class EqualToCompareOp(NumericCompareOp):
    pass


@dataclass(frozen=True)
class ComparisonExpr(BoolExpr):
    thing_1: NumberExpr
    compare_op: NumericCompareOp
    thing_2: NumberExpr


@dataclass(frozen=True)
class DemandHadEffectExpr(BoolExpr):
    desired: bool  # expr evals to True iff (whether an effect happened) == desired


@dataclass(frozen=True)
class AndExpr(BoolExpr):
    left: BoolExpr
    right: BoolExpr


@dataclass(frozen=True)
class OrExpr(BoolExpr):
    left: BoolExpr
    right: BoolExpr


@dataclass(frozen=True)
class NotExpr(BoolExpr):
    pred: BoolExpr


# ideally, AnyOne would be a single object...
# but typing that is hard. so we'll make one per
# feature.
class AnyNumber(NumberExpr, Choice):
    pass


class AnyColor(ColorExpr, Choice):
    pass


@dataclass(frozen=True)
class ValuesOfCards(NumbersExpr):
    cards: CardExpr


@dataclass(frozen=True)
class ColorsOfCards(ColorsExpr):
    cards: CardExpr


@dataclass(frozen=True)
class TupleOfColorsExpr(ColorsExpr):
    colors: Tuple[ColorExpr]


@dataclass(frozen=True)
class ColorsOnPlayerBoardExpr(ColorsExpr):
    player: PlayerExpr


@dataclass(frozen=True)
class NamesOfCards(CardNamesExpr):
    cards: CardExpr


@dataclass(frozen=True)
class ValueOfCard(NumberExpr):
    card: CardExpr


@dataclass(frozen=True)
class ColorOfCard(ColorExpr):
    card: CardExpr


@dataclass(frozen=True)
class NameOfCard(CardNameExpr):
    card: CardExpr


@dataclass(frozen=True)
class HasFeatureFunc(BoolFunc[F]):
    feature: F

    def interp(self, di) -> CardProp:
        return di.interp_hasfeaturefunc(self)


@dataclass(frozen=True)
class AndFunc(BoolFunc[T]):
    left: BoolFunc[T]
    right: BoolFunc[T]


@dataclass(frozen=True)
class OrFunc(BoolFunc[T]):
    left: BoolFunc[T]
    right: BoolFunc[T]


@dataclass(frozen=True)
class NotFunc(BoolFunc[T]):
    pred: BoolFunc[T]


@dataclass(frozen=True)
class AbstractZoneLiteral(AbstractZone):
    field: PlayerField

    def interp(self, di) -> PlayerField:
        return di.interp_abstractzoneliteral(self)


# TODO: integrate these nicely with the literals
class TopCardsZone(AbstractZone):
    pass


class BottomCardsZone(AbstractZone):
    pass  # not sure if this is needed, but I'm including it on principle


class YouExpr(PlayerExpr):
    def interp(self, di) -> PlayerState:
        return di.interp_youexpr()


class MeExpr(PlayerExpr):
    pass


class EveryoneExpr(PlayersExpr):
    pass


class EveryoneElseExpr(PlayersExpr):
    pass


class NobodyExpr(PlayersExpr):
    pass


class AnyoneExpr(PlayerExpr):
    pass


class AnyoneElseExpr(PlayerExpr):
    pass


class ChooseSomeoneExpr(PlayerExpr, Choice):
    pass


class MyChoiceOfCardExpr(CardExpr, Choice):
    pass


@dataclass(frozen=True)
class DrawStmt(Stmt):
    amount: NumberExpr  # how many cards?
    age: NumberExpr  # what age?

    def interp(self, di) -> GameState:
        return di.interp_drawstmt(self)


class DrawAndFriendlyStmtName(Enum):
    MELD = auto()
    REVEAL = auto()
    SCORE = auto()
    TUCK = auto()


@dataclass(frozen=True)
class MeldStmt(Stmt):
    cards: CardsExpr

    def interp(self, di) -> GameState:
        return di.interp_meldstmt(self)


@dataclass(frozen=True)
class RevealStmt(Stmt):
    card: CardExpr


@dataclass(frozen=True)
class ScoreStmt(Stmt):
    cards: CardsExpr

    def interp(self, di):
        return di.interp_scorestmt(self)


@dataclass(frozen=True)
class TuckStmt(Stmt):
    cards: CardsExpr


@dataclass(frozen=True)
class DrawAndStmt(DrawStmt):
    amount: NumberExpr
    age: NumberExpr
    then: DrawAndFriendlyStmtName

    def interp(self, di) -> GameState:
        return di.interp_drawandstmt(self)


@dataclass(frozen=True)
class ForStmt(Stmt):
    countable: CountableExpr
    count_by: NumberLiteralExpr
    do: Stmts


@dataclass(frozen=True)
class IfStmt(Stmt):
    condition: BoolExpr
    then_do: Stmts
    
    def interp(self, di):
        return di.interp_ifstmt(self)


@dataclass(frozen=True)
class IfElseStmt(Stmt):  # TODO: consider inheritance?
    condition: BoolExpr
    then_do: Stmts
    else_do: Stmts

    def func(self) -> GameStateTransition:
        def execute_a_path(cur_state: GameState) -> GameState:
            if self.condition.eval(cur_state):
                return self.then_do.func()(cur_state)
            else:
                return self.else_do.func()(cur_state)
        return execute_a_path


class RepeatStmt(Stmt):
    def interp(self, di):
        di.interp_repeatstmt()


@dataclass(frozen=True)
class DoXOrYStmt(Stmt):
    path_1: Stmts
    path_2: Stmts


@dataclass(frozen=True)
class YouMayStmt(Stmt):
    stmts: Stmts


@dataclass(frozen=True)
class TransferStmt(Stmt):
    cards: CardsExpr
    dest: PlayerZoneExpr


@dataclass(frozen=True)
class ReturnStmt(Stmt):
    cards: CardsExpr


@dataclass(frozen=True)
class NukeStmt(Stmt):
    cards: CardsExpr


class EndDogmaActionStmt(Stmt):
    pass


@dataclass(frozen=True)
class WinStmt(Stmt):
    winner: PlayerExpr


@dataclass(frozen=True)
class DogmaComboStmt(Stmt):
    card: CardExpr


@dataclass(frozen=True)
class SplayDirection(Expr):
    direction: Optional[structs.Splay]  # "None" means any direction


# TODO: consider restructuring
# this is a handy little product type, but
# i'm not sure we need it
@dataclass(frozen=True)
class PlayersFeatureExpr(Generic[F], Expr):
    players: PlayersExpr
    feature: F


# CHECKME
@dataclass(frozen=True)
class AnySplayedColorExpr(Choice, ColorExpr):
    player: PlayerExpr
    direction: SplayDirection


@dataclass(frozen=True)
class PileIsSplayedExpr(BoolExpr):
    player: PlayerExpr
    color: ColorExpr
    direction: SplayDirection


@dataclass(frozen=True)
class SplayStmt(Stmt):
    player: PlayersExpr
    color: ColorsExpr
    direction: SplayDirection


@dataclass(frozen=True)
class SpecialAchieveStmt(Stmt):
    name: CardNameExpr