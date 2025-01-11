from atomic_changes import *

# We implement gameplay as transition functions between the current state and a new state.


def select_turn_draw(state : GameState, pid : int) -> int:
    # find the highest top-card age on player's board
    return max((pile[-1].age for pile in state.players[pid].board.values()))


def draw_n(state : GameState, pid : int, age : int) -> GameState:
    target_deck = state.decks[age]
    # Draw from the lowest non-empty pile >= n
    while (len(target_deck) == 0) and age <= 10:
        age += 1
        target_deck = state.decks[age]
    if age == 11:
        # TODO: End the game!
        raise Exception("Game over! Endgame needs implementing.")
    drawn_card = target_deck[-1]
    return apply_funcs(state,
        [
            remove_top_card_from_deck(age),
            add_card_to_player_hand(drawn_card, pid)
        ]
    )


##### ACTIONS #####
# Players must do two of the following actions per turn.

# 1. Draw from the appropriate deck.
def do_turn_draw(state : GameState, pid : int) -> GameState:
    return draw_n(state, pid, select_turn_draw(state, pid))


# 2. Meld a card from their hand.
def meld_from_hand(state : GameState, pid : int, card : Card) -> GameState:
    return apply_funcs(state,
        [
            remove_card_from_player_hand(card, pid),
            add_card_to_player_board(card, pid, tuck=False)
        ]
    )


# 3. If possible, achieve. 
# (NOTE: If this function is being called, it assumes it's valid.)
def achieve(state : GameState, pid : int) -> GameState:
    return apply_funcs(state,
        [
            add_card_to_player_achievements(state.achievements[-1], pid),
            remove_top_public_achievement
        ]
    )


# 4. Use the top dogma effect on one of their piles.