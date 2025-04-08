from dogma_ir_typing import *
from structs import *
from typing import List, Tuple
from gameplay import draw_n

class DogmaInterpreter():
    # we're gonna go full mutable for now, but with good logging and lazy evaluation
    def __init__(self):
        self.applied_changes : List[GameStateTransition] = []
        self.unapplied_changes : List[GameStateTransition] = []  # FIXME: make this a queue


    def interpret_card(self, state: GameState, me_id: int, card: Card):
        self.state = state
        self.me_id = me_id
        self.you_id = None
        self.effects : List[GameStateTransition] = []
        for dogma_effect in card.dogmata:
            if dogma_effect.is_demand:
                self.interpret_demand_effect(dogma_effect)
            else:
                self.interpret_shared_effect(dogma_effect)


    def interpret_demand_effect(self, deffect: DEffect):
        ...

    
    def interpret_shared_effect(self, deffect: DEffect):
        self.effects = []
        num_players = len(self.state.players)
        self.you_id = (self.me_id + 1) % num_players
        my_icon_count = self.state.players[self.me_id].count_icon(deffect.key_icon)
        if self.state.debug[DFlags.GAME_LOG]:
            print(f"\tIt's a shared effect. Player {self.me_id+1} has {my_icon_count} {deffect.key_icon}.")
        for _ in range(num_players):
            your_icon_count = self.state.players[self.me_id].count_icon(deffect.key_icon)
            if my_icon_count >= your_icon_count:
                if self.state.debug[DFlags.GAME_LOG]:
                    if self.you_id != self.me_id:
                        print(f"\t\tPlayer {self.you_id+1} has {your_icon_count} {deffect.key_icon}, so it can share.")  # TODO: better pretty-printing here
                    else:
                        print(f"\t\tFinally, Player {self.me_id+1} uses the effect.")
                for stmt in deffect.effects:
                    self.interpret_stmt(stmt)  # do the dogma for that player
            else:
                if self.state.debug[DFlags.GAME_LOG]:
                    print(f"\t\tPlayer {self.you_id+1} has {your_icon_count} {deffect.key_icon}, so it cannot share.")
            self.you_id = (self.you_id + 1) % num_players  # go to the next player
        self.update_state()
    

    def update_state(self):
        if self.state.debug[DFlags.GAME_LOG]:
            print(f"\tUpdating game state...")
        while self.unapplied_changes:
            func = self.unapplied_changes[0]
            self.unapplied_changes = self.unapplied_changes[1:]  # FIXME: queue needed
            self.state = func(self.state)
            self.applied_changes.append(func)
            if self.state.winner is not None:
                return  # game over, man!


    def interpret_stmt(self, node: Stmt):
        # split across stmt types. TODO.
        try:
            return node.interp(self)
        except:
            raise Exception(f"unimplemented for type {type(node)}")
    
    
    def interp_drawstmt(self, node: DrawStmt):
        amount = node.amount.interp(self)
        age = node.age.interp(self)
        you = self.you_id
        for _ in range(amount):
            self.unapplied_changes.append(
                lambda state: draw_n(state, you, age)
            )


    def interp_numberliteralexpr(self, node: NumberLiteralExpr) -> int:
        return node.number