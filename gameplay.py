from atomic_changes import *
from debug_handler import DFlags

# We implement gameplay as transition functions between the current state and a new state.


def select_turn_draw(state : GameState, pid : int) -> int:
    # find the highest top-card age on player's board.
    # if they have no cards, it's 1.
    turn_draw : int = 1
    board = state.players[pid].board
    for color in Color:
        if len(board[color]) > 0:
            top_age = board[color].top().age
            turn_draw = max(top_age, turn_draw)
    return turn_draw


# Draw one card of a given age.
def draw_n(state : GameState, pid : int, age : int) -> GameState:
    # Draw from the lowest non-empty pile >= n
    if state.debug[DFlags.GAME_LOG]:
        old_age = age

    while (age <= 10) and (len(state.decks[age]) == 0):
        age += 1
    if age == 11:
        # the game is over!
        if state.debug[DFlags.GAME_LOG]:
            print(f"Player {pid+1} tried to draw an 11!")
        state.winner = pid
        return state
    drawn_card = state.decks[age][-1]

    if state.debug[DFlags.GAME_LOG]:
        drawn_str = f"[{old_age}]"
        if age != old_age:
            drawn_str += f" (--> [{age}])"
        print(f"\t\tPlayer {pid+1} draws a {drawn_str}:")
        print(f"\t\t\t{drawn_card}")

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
    if state.debug[DFlags.GAME_LOG]:
        print(f"Player {pid+1} melds {card} from their hand.")
    return apply_funcs(state,
        [
            remove_card_from_player_hand(card, pid),
            add_card_to_player_board(card, pid, False)  # not tucked
        ]
    )
    

# 3. If possible, achieve. 
# (NOTE: If this function is being called, it assumes it's valid.)
def achieve(state : GameState, pid : int) -> GameState:
    # TODO: DFlags.GAME_LOG print
    return apply_funcs(state,
        [
            add_card_to_player_achievements(state.achievements[-1], pid),
            remove_top_public_achievement
        ]
    )