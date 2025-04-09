from atomic_changes import *
from debug_handler import DFlags
from typing import Tuple
from structs import *

# We implement gameplay as transition functions between the current state and a new state.
# TODO: these probably shouldn't be static functions


@assume_partial
def score_card_from_pid_field(card: Card, scoring_pid: PlayerId, source_pid: PlayerId, source_field: PlayerField, state: GameState) -> GameState:
    # TODO: make this neater
    # probably means reimplementing remove_card_from_loc
    if source_field == PlayerField.BOARD:
        remove_func = remove_card_from_player_board(card, source_pid)
    elif source_field == PlayerField.HAND:
        remove_func = remove_card_from_player_hand(card, source_pid)
    elif source_field == PlayerField.SCORE_PILE:
        remove_func = remove_card_from_player_score(card, source_pid)
    else:
        remove_func = lambda state: "Can't remove card from PlayerField {field}" // 0
    return apply_funcs(state, [
        remove_func,
        add_card_to_player_score(card, scoring_pid)
    ])
    


def select_turn_draw(state : GameState, pid : PlayerId) -> int:
    # find the highest top-card age on player's board.
    # if they have no cards, it's 1.
    turn_draw : Age = 1
    board = state.players[pid].board
    for color in Color:
        if len(board[color]) > 0:
            top_age = board[color].top().age
            turn_draw = max(top_age, turn_draw)
    return turn_draw


# Draw one card of a given age.
def draw_n(state : GameState, pid : PlayerId, age : Age) -> Tuple[GameState, Card]:
    # Draw from the lowest non-empty pile >= n
    if state.debug[DFlags.GAME_LOG]:
        old_age = age

    while (age <= 10) and (len(state.decks[age]) == 0):
        if state.debug[DFlags.GAME_LOG]:
            print(f"The [{age}] pile is empty.")
        age += 1
    if age == 11:
        # the game is over!
        if state.debug[DFlags.GAME_LOG]:
            print(f"{state.players[pid].name} tried to draw an 11!")
        state.winner = pid
        return (state, None)
    drawn_card = state.decks[age][-1]

    return (apply_funcs(state,
        [
            remove_top_card_from_deck(age),
            add_card_to_player_hand(drawn_card, pid)
        ]
    ), drawn_card)


##### ACTIONS #####
# Players must do two of the following actions per turn.

# 1. Draw from the appropriate deck.
def do_turn_draw(state : GameState, pid : PlayerId) -> Tuple[GameState, Card]:
    return draw_n(state, pid, select_turn_draw(state, pid))


# 2. Meld a card from their hand.
def meld_from_hand(state : GameState, pid : PlayerId, card : Card) -> Tuple[GameState, Card]:
    return (apply_funcs(state,
        [
            remove_card_from_player_hand(card, pid),
            add_card_to_player_board(card, pid, False)  # not tucked
        ]
    ), card)
    

# 3. If possible, achieve. 
# (NOTE: If this function is being called, it assumes it's valid.)
def achieve(state : GameState, pid : PlayerId) -> GameState:
    # TODO: DFlags.GAME_LOG print
    return apply_funcs(state,
        [
            add_card_to_player_achievements(state.achievements[-1], pid),
            remove_top_public_achievement
        ]
    )