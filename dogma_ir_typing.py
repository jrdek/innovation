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


class IRTreeNode:
    def __str_helper__(self) -> List[Union[str, List]]:  # TODO: type better
        out_list = [type(self).__name__]
        for key, value in self.__dict__.items():
            value_repr = value.__str_helper__() if isinstance(value, IRTreeNode) else [str(value)]
            out_list.append((key, value_repr) if len(value_repr) > 1 else [f"{key}={value_repr[0]}"])
        return out_list

    def __str__(self):
        # handle indentation here
        INDENT = '  '
        outstr = ""
        recursed_list = self.__str_helper__()
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


class BoolExpr(Expr):
    pass


class NumberExpr(Expr):
    pass


# TODO: IconsExpr?


class IconExpr(Expr):
    pass


class ColorExpr(Expr):
    pass


class CardsExpr(Expr):
    pass


class CardExpr(CardsExpr):  # TODO: evaluate design here
    pass


class PlayerExpr(Expr):
    pass


class ReferentExpr(Expr):
    """
    NOTE. In our grammar, the referents are
    - it / them (basically the same semantically)
    - the chosen one(s)
    - the other one(s)

    For now, I'm choosing to have the interpreter decide a referent's type at runtime.
    The card grammar is unambiguous enough to make not just the type, but
    the *antecedent* of a referent clear to a human player interpreting the
    card, so I'll trust it.
    """
    pass


class ThoseOnesExpr(ReferentExpr):
    pass


class OtherOnesExpr(ReferentExpr):
    pass


class ChosenOnesExpr(ReferentExpr):
    pass



class Quantifier:
    pass

class AnyQuantifier(Quantifier):
    pass

class AllQuantifier(Quantifier):
    pass


@dataclass
class CardsAreLikeExpr(BoolExpr, ABC):
    quantifier: Optional[Quantifier]
    cards: CardsExpr


@dataclass
class CardsHaveIconExpr(CardsAreLikeExpr):
    icon: IconExpr


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
class UpToNumberExpr(NumberExpr):
    # user must choose how many, up to [num].
    pass


@dataclass
class CardNameExpr(CardExpr):  # CardExpr because you can refer to cards by their names
    name: str


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


@dataclass
class RepeatStmt(Stmt):
    pass






