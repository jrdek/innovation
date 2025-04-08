"""
I'm essentially writing a compiler:
    Input: Card definitions (expressed in an easily-parsed subset of English)
    Output: Functions which take a GameState and return a new GameState

A type system will be valuable here, especially because sometimes players
have to choose things of a given type!

The point of the IR is to translate our Lark tree into just everyday Python.
Instead of "tree nodes" having a .children list, they will have named fields.
"""

from abc import ABC  # TODO: do I actually *need* ABCs here? i suspect not
from typing import List, Union, Optional, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum, auto
import structs
import lark
from collections.abc import Callable
from frozenlist import FrozenList


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
class Stmts(IRTreeNode, FrozenList[Stmt]):  # TODO: This is breaking some or other idiom. Does this *have* a List, or *is* it a List?
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


class Expr(IRTreeNode):
    pass

class CardFeature(Expr):
    pass

T = TypeVar(name="T")
F = TypeVar(name="F", bound=CardFeature)


class Quantifier(IRTreeNode):
    pass

class AnyQuantifier(Quantifier):
    pass

class NoneQuantifier(Quantifier):
    pass

class AllQuantifier(Quantifier):
    pass


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

class NumbersExpr(CountableExpr, CardFeature):
    pass


class NumberExpr(NumbersExpr):
    pass


class AllNumberExpr(NumberExpr):
    pass

@dataclass
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


class CardsExpr(CountableExpr):
    pass

class CardExpr(CardsExpr):  # TODO: evaluate design here
    pass

class PlayersExpr(CountableExpr):
    pass

class PlayerExpr(PlayersExpr):
    pass
    

class AbstractZone(IRTreeNode):
    pass


class ReferentExpr(CardExpr):
    """
    NOTE. In our grammar, the referents are
    - it / them (basically the same semantically)
    - the chosen one(s)
    - the other one(s)

    For now, I'm choosing to have the interpreter decide a referent's type at runtime.
    The card grammar is unambiguous enough to make not just the type, but
    the *antecedent* of a referent clear to a human player interpreting the
    card, so I'll trust it.

    TODO: (end of day 4/4) I'm seriously reconsidering this...
    """
    pass


class ThoseOnesExpr(ReferentExpr):
    pass


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


@dataclass
class PlayerZoneExpr(Expr):
    player: PlayerExpr
    zone: AbstractZone


FeaturesLike = BoolFunc[CardFeature]

class AnyFeatures(FeaturesLike):
    pass

class SelectionLambda(IRTreeNode):
    pass

class AnySelection(SelectionLambda):
    pass

class Superlative(SelectionLambda):
    pass

class HighestSuperlative(Superlative):
    pass

class LowestSuperlative(Superlative):
    pass

@dataclass
class ExtremeValueExpr(NumberExpr):
    superlative: Superlative
    zone: PlayerZoneExpr

class ColorsOnOnlyYourBoardExpr(ColorsExpr):
    pass

# How many of which cards are we selecting?
# (FIXME: kw_only is a hack to allow subclasses with non-default args)
@dataclass(kw_only=True)
class ZonelessSelectionStrategy(IRTreeNode):
    num: NumberExpr = AllNumberExpr()
    selection_lambda: SelectionLambda = AnySelection()

# From where?
@dataclass
class ZonedSelectionStrategy(ZonelessSelectionStrategy):
    src: PlayerZoneExpr



@dataclass
class CardsAreLikeExpr(BoolExpr, ABC):
    cards: CardsExpr
    like: FeaturesLike
    quantifier: Optional[Quantifier] = AnyQuantifier()  # CHECKME: not all?


@dataclass
class CountExpr(NumberExpr):
    countable: CountableExpr


class PointsExpr(NumberExpr):
    pass


@dataclass
class NumberLiteralExpr(NumberExpr):
    number: int


@dataclass
class IconLiteralExpr(IconExpr):
    icon: structs.Icon


@dataclass
class ColorLiteralExpr(ColorExpr):
    color: structs.Color


@dataclass
class ChooseUpToNumberExpr(NumberExpr, Choice):
    # user must choose how many, up to [num].
    upper_bound: NumberExpr


@dataclass
class SumExpr(NumberExpr):
    left: NumberExpr
    right: NumberExpr

@dataclass
class ProductExpr(NumberExpr):
    left: NumberExpr
    right: NumberExpr

class RoundDir(IRTreeNode):
    pass

class RoundedUp(RoundDir):
    pass

class RoundedDown(RoundDir):
    pass

@dataclass
class QuotientExpr(NumberExpr):
    dividend: NumberExpr
    divisor: NumberExpr
    round_dir: RoundDir = RoundedDown()

@dataclass
class PlayerScoreExpr(NumberExpr):
    player: PlayerExpr



class NoCondition(BoolExpr):
    pass

@dataclass
class ZonelessCardsThatExpr(CardsExpr):
    that: FeaturesLike
    strat: Optional[ZonelessSelectionStrategy] = None  # TODO: de-Noneify this
    condition: BoolExpr = NoCondition()

# TODO: should this inherit from ZonelessCardsThat?
@dataclass
class CardsThatExpr(CardsExpr):
    that: FeaturesLike
    strat: Optional[ZonedSelectionStrategy] = None # TODO: what to do if this is None?
    condition: BoolExpr = NoCondition()
    

@dataclass
class IconsInCardsExpr(NumberExpr):
    icons: IconsExpr
    cards: CardsThatExpr


class CardNamesExpr(CardExpr, CardFeature):  # CardExpr because you can refer to cards by their names
    pass

@dataclass
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


@dataclass
class ComparisonExpr(BoolExpr):
    thing_1: NumberExpr
    compare_op: NumericCompareOp
    thing_2: NumberExpr


# intuition: eval quantifier(set of players who transferred cards)
@dataclass
class CardsWereTransferredExpr(BoolExpr):
    actor: PlayersExpr


@dataclass
class AndExpr(BoolExpr):
    left: BoolExpr
    right: BoolExpr

@dataclass
class OrExpr(BoolExpr):
    left: BoolExpr
    right: BoolExpr

@dataclass
class NotExpr(BoolExpr):
    pred: BoolExpr

# ideally, AnyOne would be a single object...
# but typing that is hard. so we'll make one per
# feature.
class AnyNumber(NumberExpr, Choice):
    pass

class AnyColor(ColorExpr, Choice):
    pass

@dataclass
class ValuesOfCards(NumbersExpr):
    cards: CardExpr

@dataclass
class ColorsOfCards(ColorsExpr):
    cards: CardExpr

@dataclass
class ListOfColorsExpr(ColorsExpr):
    colors: List[ColorExpr]

@dataclass
class ColorsOnPlayerBoardExpr(ColorsExpr):
    player: PlayerExpr

@dataclass
class NamesOfCards(CardNamesExpr):
    cards: CardExpr

@dataclass
class ValueOfCard(NumberExpr):
    card: CardExpr

@dataclass
class ColorOfCard(ColorExpr):
    card: CardExpr

@dataclass
class NameOfCard(CardNameExpr):
    card: CardExpr


@dataclass
class HasFeatureFunc(BoolFunc[F]):
    feature: F

# TODO: does this require separate and/or/not
# types from just the *boolean* and/or/not?

@dataclass
class AndFunc(BoolFunc[T]):
    left: BoolFunc[T]
    right: BoolFunc[T]

@dataclass
class OrFunc(BoolFunc[T]):
    left: BoolFunc[T]
    right: BoolFunc[T]

@dataclass
class NotFunc(BoolFunc[T]):
    pred: BoolFunc[T]

@dataclass
class AbstractZoneLiteral(AbstractZone):
    field: structs.PlayerField

# TODO: integrate these nicely with the literals
class TopCardsZone(AbstractZone):
    pass

class BottomCardsZone(AbstractZone):
    pass  # not sure if this is needed, but I'm including it on principle


class YouExpr(PlayerExpr):
    pass

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


@dataclass
class DrawStmt(Stmt):
    amount: Union[NumberExpr, ChooseUpToNumberExpr]  # how many cards?
    age: NumberExpr  # what age?

class DrawAndFriendlyStmtName(Enum):
    MELD = auto()
    REVEAL = auto()
    SCORE = auto()
    TUCK = auto()

@dataclass
class MeldStmt(Stmt):
    cards: CardsExpr

@dataclass
class RevealStmt(Stmt):
    card: CardExpr

@dataclass
class ScoreStmt(Stmt):
    cards: CardsExpr

@dataclass
class TuckStmt(Stmt):
    cards: CardsExpr

@dataclass
class DrawAndStmt(Stmt):
    then: DrawAndFriendlyStmtName
    amount: Union[NumberExpr, ChooseUpToNumberExpr]
    age: NumberExpr



@dataclass
class ForStmt(Stmt):
    countable: CountableExpr
    count_by: NumberLiteralExpr
    do: Stmts

@dataclass
class IfStmt(Stmt):
    condition: BoolExpr
    then_do: Stmts

@dataclass
class IfElseStmt(Stmt):  # TODO: consider inheritance?
    condition: BoolExpr
    then_do: Stmts
    else_do: Stmts

class RepeatStmt(Stmt):
    pass


@dataclass
class DoXOrYStmt(Stmt):
    path_1: Stmts
    path_2: Stmts


@dataclass
class YouMayStmt(Stmt):
    stmts: Stmts


@dataclass
class TransferStmt(Stmt):
    cards: CardsExpr
    dest: PlayerZoneExpr


@dataclass
class ReturnStmt(Stmt):
    cards: CardsExpr

@dataclass
class NukeStmt(Stmt):
    cards: CardsExpr

class EndDogmaActionStmt(Stmt):
    pass

@dataclass
class WinStmt(Stmt):
    winner: PlayerExpr


@dataclass
class DogmaComboStmt(Stmt):
    card: CardExpr

@dataclass
class SplayDirection(Expr):
    direction: Optional[structs.Splay]  # "None" means any direction


# TODO: consider restructuring
# this is a handy little product type, but
# i'm not sure we need it

@dataclass
class PlayersFeatureExpr(Generic[F], Expr):
    players: PlayersExpr
    feature: F

# CHECKME
@dataclass
class AnySplayedColorExpr(Choice, ColorExpr):
    player: PlayerExpr
    direction: SplayDirection

@dataclass
class PileIsSplayedExpr(BoolExpr):
    player: PlayerExpr
    color: ColorExpr
    direction: SplayDirection

@dataclass
class SplayStmt(Stmt):
    player: PlayersExpr
    color: ColorsExpr
    direction: SplayDirection

@dataclass
class SpecialAchieveStmt(Stmt):
    name: CardNameExpr