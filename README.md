[TODO: Formalize.]

In Innovation (like in other turn-based games), moves that can be taken result in the state of the game changing.
To implement this, state changes are represented here as lambdas which take a GameState and return a subsequent GameState.

Something, however, needs to actually apply the state changes and track the current "active" state.
This is the high-level purpose of the Director object, contained in this folder.

The Director is also what coordinates interaction with the PlayerAgents.

I'm implementing this (at least at a basic level) prior to finishing dogmas, because in essence, all we need to handle is the actions in gameplay.py:

---

On a turn, the active player must take a first action, then a second action.
Actions are one of:
    - Do a turn-draw;
    - If any cards in hand, select a card from hand and meld it.
    - If any cards on board, select a top card from board and dogma it.
Then the active player increments (mod # players).

---



