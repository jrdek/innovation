from game_state import *
from dogma_behavior import *
import dataclasses as dc
from typing import List, Set, Union, Deque, Type
from collections.abc import Callable
from functools import partial
from inspect import signature

"""
When a player melds a card from their hand, two things happen "at once":
1. The card is removed from their hand.
2. The card is placed on the corresponding stack on their board.

In order to make writing player actions easier, we implement each step as its own function.
Notably, *these functions should NEVER be used directly by a PlayerAgent!* They do not 
consider the legality of a move.

All functions which impact gameplay take a GameState as an argument, then construct and
return the state which results from taking a given action. (i.e., they're all pure!)
"""


# TODO: What's a better type signature for this?
def apply_funcs(t : any, fs : List[Callable]) -> any:
    for f in fs:
        t = f(t)
    return t


# decorator to assume that a function is partial if not all args
# are supplied.
# NOTE: this might break if func uses *args/**kwargs
def assume_partial(func):
    num_params = len(signature(func).parameters)
    def wrapper(*args):
        if len(args) < num_params:
            # TODO: is this bad?
            subfunc = assume_partial(partial(func, *args))
            return subfunc
        else:
            return func(*args)  # throws error if too many args
    return wrapper


# TODO: Check that all of these are deep-copying

##### ADD A CARD TO A ZONE #####

@assume_partial
def assign_card_owner(id : Optional[int], card : Card) -> Card:
    return dc.replace(card, owner=id)


@assume_partial
def add_card_to_deque(tuck : bool, d : Deque[Card], card : Card) -> Deque[Card]:
    # the top card is idx -1; the bottom card is idx 0
    # (we're doing this instead of appending because of function purity!)
    if tuck: 
        return deque([card, *d])
    else:
        return d + deque([*d, card])
    

@assume_partial
def add_card_to_pile(tuck : bool, pi : Pile, card : Card) -> Pile:
    new_deque = add_card_to_deque(tuck, deque(pi), card)
    return dc.replace(pi, cards=new_deque)


@assume_partial
def add_card_to_list(xs : List[Card], card : Card) -> List[Card]:
    return [*xs, card]


@assume_partial
def show_card(card : Card) -> Card:
    return dc.replace(card, faceup=True)


@assume_partial
def hide_card(card : Card) -> Card:
    return dc.replace(card, faceup=False)


CardLoc = Union[List[Card], Pile, Deque]


@assume_partial
def container_fail(dest : CardLoc, card : Card):
    raise TypeError(f"Unhandled container type {type(dest)}")


def add_card_to_loc(card : Card, owner_id : int, dest : CardLoc, faceup : bool, tuck=False):
    if type(dest) is deque:
        add_func = add_card_to_deque(tuck)
    elif type(dest) is Pile:
        add_func = add_card_to_pile(tuck)
    elif type(dest) is list:
        add_func = add_card_to_list
    else:
        add_func = container_fail
    
    if faceup:
        show_func = show_card
    else:
        show_func = hide_card

    return apply_funcs(
        card,
        [
            show_func,
            assign_card_owner(owner_id),
            add_func(dest)
        ]
    )


@assume_partial
def add_card_to_player_hand(card : Card, pid : int, state : GameState) -> GameState:
    return dc.replace(state,
        players=[
            p if i != pid else dc.replace(p, 
                hand=add_card_to_loc(card, owner_id=pid, dest=p.hand, faceup=False)
            ) for (i,p) in enumerate(state.players)
        ]
    )


@assume_partial
def add_card_to_player_score(card : Card, pid : int, state : GameState) -> GameState:
    return dc.replace(state,
        players=[
            p if i != pid else dc.replace(p, 
                scored_cards=add_card_to_loc(card, owner_id=pid, dest=p.scored_cards, faceup=False)
            ) for (i,p) in enumerate(state.players)
        ]
    )


@assume_partial
def add_card_to_player_achievements(card : Card, pid : int, state : GameState) -> GameState:
    return dc.replace(state,
        players=[
            p if i != pid else dc.replace(p, 
                achieved_cards=add_card_to_loc(card, owner_id=pid, dest=p.achieved_cards, faceup=False)
            ) for (i,p) in enumerate(state.players)
        ]
    )


@assume_partial
def add_card_to_player_board(card : Card, pid : int, tuck : bool, state : GameState) -> GameState:
    return dc.replace(state,
        players=[
            p if i != pid else dc.replace(p,
                board={
                    **p.board,
                    card.color: add_card_to_loc(card, owner_id=pid, dest=p.board[card.color], faceup=True, tuck=tuck)
                }
            ) 
            for (i, p) in enumerate(state.players)
        ]
    )


@assume_partial
def gain_special_achievement(sa : SpecialAchievement, pid : int, state : GameState) -> GameState:
    return dc.replace(state,
        players = [
            p if i != pid else dc.replace(p, 
                special_achievements=p.special_achievements.union({sa})
            ) for (i,p) in enumerate(state.players)
        ]
    )


@assume_partial
def add_card_to_deck(card : Card, tuck : bool, state : GameState) -> GameState:
    return dc.replace(state,
        decks=[
            d if i != card.age else add_card_to_loc(card, owner_id=0, dest=d, faceup=False, tuck=tuck)
            for (i, d) in enumerate(state.decks)
        ]
    )


@assume_partial
def add_card_to_global_achievements(card : Card, state : GameState) -> GameState:
    return dc.replace(state,
        achievements=add_card_to_loc(card, owner_id=0, dest=state.achievements, faceup=False)
    )


##### REMOVE A CARD FROM A ZONE #####
# this is way, way simpler than adding

def remove_card_from_loc(card : Card, dest : CardLoc) -> CardLoc:
    if card not in dest:
        raise ValueError("Card not found in "+str(dest))
    try:
        new_dest = type(dest)([c for c in dest if c != card])
        if type(new_dest) is Pile:
            new_dest.splay = dest.splay
        return new_dest
    except:  # TODO specify exception
        container_fail()


@assume_partial
def remove_top_card_from_deck(age : int, state : GameState) -> GameState:
    return dc.replace(state,
        decks=[
            d if i != age else d[:-1]  # no need for the helper func here
            for (i, d) in enumerate(state.decks)
        ]
    )


@assume_partial
def remove_top_public_achievement(state : GameState) -> GameState:
    return dc.replace(state,
        achievements=state.achievements[:-1]
    )


@assume_partial
def remove_card_from_player_hand(card : Card, pid : int, state : GameState) -> GameState:
    return dc.replace(state,
        players=[
            p if i != pid else dc.replace(p, 
                hand=remove_card_from_loc(card, p.hand)
            ) for (i,p) in enumerate(state.players)
        ]
    )


@assume_partial
def remove_card_from_player_score(card : Card, pid : int, state : GameState) -> GameState:
    return dc.replace(state,
        players=[
            p if i != pid else dc.replace(p, 
                scored_cards=remove_card_from_loc(card, p.scored_cards)
            ) for (i,p) in enumerate(state.players)
        ]
    )
