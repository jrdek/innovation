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


T = TypeVar(name="T")  # TODO: constrain maybe


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
            if isinstance(value, IRTreeNode):
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
class Stmts(IRTreeNode, List[Stmt]):  # TODO: This is breaking some or other idiom. Does this *have* a List, or *is* it a List?
    def __str_helper__(self):
        return [stmt.__str_helper__() for stmt in self]
    
    def __str__(self):  
        return '\n'.join(str(stmt) for stmt in self)


class Expr(IRTreeNode):
    pass


class Quantifier(IRTreeNode):
    pass

class AnyQuantifier(Quantifier):
    pass

class AllQuantifier(Quantifier):
    pass


class CountableExpr(Expr):
    pass


class BoolExpr(Expr):
    pass


class NumberExpr(CountableExpr, Quantifier):
    # TODO: should I feel weird about numbers being quantifiers?
    pass


class IconsExpr(CountableExpr):
    pass

class IconExpr(IconsExpr):
    pass


class ColorsExpr(CountableExpr):
    pass

class ColorExpr(ColorsExpr):
    pass


class CardsExpr(CountableExpr):
    pass

class CardExpr(CardsExpr):  # TODO: evaluate design here
    pass


class PlayerExpr(CountableExpr):
    pass
    

class AbstractZone(IRTreeNode):
    pass


class ReferentExpr(CountableExpr):
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







class PileLoc(IRTreeNode):
    pass

class BottomOfPile(PileLoc):
    pass

class TopOfPile(PileLoc):
    pass


@dataclass
class PlayerZoneExpr(Expr):
    player: PlayerExpr
    zone: AbstractZone


@dataclass
class FeaturesLike(IRTreeNode):
    pile_loc: Optional[PileLoc] = None
    is_color: Optional[ColorsExpr] = None
    not_color: Optional[ColorsExpr] = None
    has_icon: Optional[IconsExpr] = None
    without_icon: Optional[IconsExpr] = None
    in_zone: Optional[PlayerZoneExpr] = None


@dataclass
class CardsAreLikeExpr(BoolExpr, ABC):
    cards: CardsExpr
    like: FeaturesLike
    quantifier: Optional[Quantifier] = None


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

class AnyColorExpr(ColorExpr):
    pass



@dataclass
class UpToNumberExpr(NumberExpr):
    # user must choose how many, up to [num].
    pass



class SelectionLambda(IRTreeNode):
    pass

class Superlative(SelectionLambda):
    pass

class HighestSuperlative(Superlative):
    pass

class LowestSuperlative(Superlative):
    pass


# How many of which cards are we selecting?
@dataclass
class SelectionStrategy(IRTreeNode):
    num: Optional[NumberExpr] = None # None means all of them
    selection_lambda: Optional[SelectionLambda] = None


@dataclass
class CardsThatExpr(CardsExpr):
    that: FeaturesLike
    strat: Optional[SelectionStrategy] = None
    


@dataclass
class CardNameExpr(CardExpr):  # CardExpr because you can refer to cards by their names
    name: str

class NumericCompareOp(IRTreeNode):
    pass

class BelowCompareOp(NumericCompareOp):
    pass

class AtLeastCompareOp(NumericCompareOp):
    pass


@dataclass
class ComparisonExpr(BoolExpr):
    thing_1: NumberExpr
    compare_op: NumericCompareOp
    thing_2: NumberExpr


class HandZone(AbstractZone):
    pass

class ScoreZone(AbstractZone):
    pass

class AchievementsZone(AbstractZone):
    pass

class BoardZone(AbstractZone):
    pass

class TopCardsZone(AbstractZone):
    pass

class BottomCardsZone(AbstractZone):
    pass  # not sure if this is needed, but I'm including it on principle


class YouExpr(PlayerExpr):
    pass

class MeExpr(PlayerExpr):
    pass


class MyChoiceOfCardExpr(CardExpr, Choice):
    pass


@dataclass
class DrawStmt(Stmt):
    amount: Union[NumberExpr, UpToNumberExpr]  # how many cards?
    age: NumberExpr  # what age?


@dataclass
class RevealStmt(Stmt):
    card: CardExpr


@dataclass
class IfStmt(Stmt):
    condition: BoolExpr
    then_do: Stmts


@dataclass
class ScoreStmt(Stmt):
    cards: CardsExpr


class RepeatStmt(Stmt):
    pass


@dataclass
class YouMayStmt(Stmt):
    path_1 : Stmts
    path_2 : Optional[Stmts] = None


@dataclass
class ReturnStmt(Stmt):
    cards: CardsExpr

@dataclass
class MeldStmt(Stmt):
    cards: CardsExpr

