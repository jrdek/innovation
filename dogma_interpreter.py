from dogma_ir_typing import *
from structs import *
from typing import List, Tuple
from agent_liaison import AgentLiaison
from game_manager import GameManager
from debug_handler import DFlags
import copy


"""
TODO:
- verify that this isn't dependent on the GM being an IGM
- reorganize the functions' order in the file (they're scattered right now)
"""


class DogmaInterpreter():
    # this interpreter evaluates eagerly (lazy impl was very hard)
    # and is extremely mutable
    def __init__(self, liaison: AgentLiaison):
        self.liaison: AgentLiaison = liaison
        self.applied_changes : List[GameStateTransition] = []
        self.antecedent : List = []
        self.antecedent_zones: List[Tuple[PlayerId, PlayerField]] = []
        self.other_player_acted: bool

    
    def you(self) -> str:
        return self.game.pid_name(self.you_id)
    

    def me(self) -> str:
        return self.game.pid_name(self.me_id)
    

    # every CardsExpr must implement .get_zones()
    def get_referentexpr_zones(self) -> List[Tuple[PlayerId, PlayerField]]:
        return self.antecedent_zones


    def get_zonelesscardsthatexpr_zones(self, node: ZonelessCardsThatExpr) -> List[Tuple[PlayerId, PlayerField]]:
        # TODO
        raise Exception("(unimplemented)")


    def get_cardsthatexpr_zones(self, node: CardsThatExpr) -> List[Tuple[PlayerId, PlayerField]]:
        if node.strat is None:
            raise Exception("unhandled: self.strat is None")
        # TODO: memoize...
        # This currently duplicates work interp-ing the tree.
        return tuple([node.strat.src.interp()]) * len(node.interp())
        

    def get_loc(self, pid: PlayerId, field: PlayerField) -> CardIdLoc:
        # TODO: handle for quick lookup on board vs in specific piles!
        # also restructure the PlayerState class to make this more ergonomic.
        # in general, this is an unsatisfying structure...
        player = self.game._state.players[pid]
        if field == PlayerField.HAND:
            return player.hand
        elif field == PlayerField.BOARD:
            return player.board
        elif field == PlayerField.SCORE_PILE:
            return player.scored_cards
        elif field == PlayerField.ACHIEVEMENTS_PILE:
            return player.achieved_cards
        else:
            raise Exception(f"Undefined PlayerField: {field}")


    def interpret_card(self, game: GameManager, me_id: int, card: Card, is_combo: bool):
        # NOTE: this function returns nothing.
        # `self.game._state` holds the fully-interpreted state.
        self.applied_changes.clear()  # TODO: maybe scrap this for now...

        # strategy: keep and maintain a local copy of the game.
        # (remember that game "change" logic is done via a manager's methods!)
        # this doesn't actually need to be maintained outside of dogma actions,
        # so we just make a new one each call of interpret_card(), then delete
        # it at the end.
        self.game = copy.deepcopy(game)

        # funny bug which will only happen with stateful PlayerAgents:
        # we still need to consume agent choices!
        self.game.liaison = game.liaison

        self.me_id = me_id
        self.you_id = me_id  # TODO
        self.antecedent.clear()
        self.other_player_acted = False
        for dogma_effect in card.dogmata:
            self.this_effect: DEffect = dogma_effect
            if dogma_effect.is_demand and not is_combo:
                self.interpret_demand_effect(dogma_effect)
            else:
                self.interpret_shared_effect(dogma_effect, is_combo)
        
        final_state = self.game._state
        del self.game
        return final_state


    def interpret_demand_effect(self, deffect: DEffect):
        ...  # TODO

    
    def interpret_shared_effect(self, deffect: DEffect, is_combo: bool):
        num_players = len(self.game._state.players)
        self.you_id = (self.me_id + 1) % num_players
        my_icon_count = self.game._state.players[self.me_id].count_icon(self.game.card_store, deffect.key_icon)
        if self.game.debug[DFlags.GAME_LOG]:
            print(f"\tIt's a shared effect. {self.me()} has {my_icon_count} {deffect.key_icon}.")
        for _ in range(num_players):
            if not is_combo or self.you_id == self.me_id:
                your_icon_count = self.game._state.players[self.you_id].count_icon(self.game.card_store, deffect.key_icon)
                if your_icon_count >= my_icon_count:
                    if self.game.debug[DFlags.GAME_LOG]:
                        if self.you_id != self.me_id:
                            print(f"\t\t{self.you()} has {your_icon_count} {deffect.key_icon}, so it can share.")  # TODO: better pretty-printing here
                        else:
                            print(f"\t\tFinally, {self.me()} uses the effect.")
                    for stmt in deffect.effects:
                        self.interp_stmt(stmt)  # do the dogma for that player
                        if self.game.winner is not None:
                            return  # game over, man!
                else:
                    if self.game.debug[DFlags.GAME_LOG]:
                        print(f"\t\t{self.you()} has {your_icon_count} {deffect.key_icon}, so it cannot share.")
            self.you_id = (self.you_id + 1) % num_players  # go to the next player
        if self.other_player_acted:
            if self.game.debug[DFlags.GAME_LOG]:
                print(f"\tSomeone shared the effect, so {self.me()} takes a turn draw:")
            self.game.turn_draw(self.me_id)
        return


    def interp_stmt(self, node: Stmt):
        # split across stmt types. TODO.
        old_state = self.game._state
        node.interp(self)
        if (self.game._state != old_state) and self.you_id != self.me_id:
            self.other_player_acted = True
        return

    
    def interp_drawstmt(self, node: DrawStmt):
        amount = node.amount.interp(self)
        age = node.age.interp(self)
        you = self.you_id

        self.antecedent = self.game.draw(you, age, amount)
        self.antecedent_zones = [(self.you_id, PlayerField.HAND)] * amount

    
    def interp_scorestmt(self, node: ScoreStmt):
        cards: List[Card] = node.cards.interp(self)
        cards_zones: List[Tuple[PlayerId, PlayerField]] = node.cards.get_zones(self)
        owners: List[PlayerId] = [zone[0] for zone in cards_zones]
        src_fields: List[PlayerField] = [zone[1] for zone in cards_zones]
        you: int = self.you_id
        
        self.game.score(cards, you, owners, src_fields)    

        self.antecedent = cards
        self.antecedent_zones = [(self.you_id, PlayerField.SCORE_PILE)] * len(cards)

    
    # TODO: make an update_antecedent macro
    def interp_meldstmt(self, node: MeldStmt):
        cards = node.cards.interp(self)
        you: int = self.you_id
        self.game.meld(you, cards, PlayerField.HAND)
        self.antecedent = cards
        self.antecedent_zones = self.you_id, PlayerField.BOARD

    
    def interp_ifstmt(self, node: IfStmt):
        condition: bool = node.condition.interp(self)
        if condition:
            node.then_do.interp(self)
        # otherwise nothing


    def interp_cardsarelikeexpr(self, node: CardsAreLikeExpr) -> bool:
        card_ids: List[CardId] = node.cards.interp(self)
        cards: List[Card] = [self.game.card_store.get(cid) for cid in card_ids]
        like: CardProp = node.like.interp(self)
        quantifier: Callable[[List[T]], bool] = node.quantifier.interp(self)
        print(f"\t\t\t\t[{', '.join(str(card) + ': ' + str(like(card)) for card in cards)}]")
        return quantifier([like(card) for card in cards])
    

    def interp_hasfeaturefunc(self, node: HasFeatureFunc) -> CardProp:
        # TODO: neaten typing casework
        # also TODO: "if it is purple or yellow"...
        feature = node.feature.interp(self)
        if isinstance(feature, Icon):
            if self.game.debug[DFlags.GAME_LOG]:
                print(f"\t\t\tDoes it have {str(feature)}?")
            return lambda card: feature in card.icons
        raise Exception(f"unimplemented feature type {type(feature)}")


    def interp_cardsthatexpr(self, node: CardsThatExpr) -> List[CardId]:
        that : CardProp = node.that.interp(self)
        strat : EvaluatedZonedSelectionStrategy = node.strat.interp(self)
        condition : bool = node.condition.interp(self)  # TODO: what to do with condition?
        
        loc = self.get_loc(strat.pid, strat.field)
        card_choices = [card_id for card_id in loc if that(self.game.card_store.get(card_id))]
        all_selected = []
        for _ in range(strat.num):
            item_selected = strat.selection_lambda(card_choices)
            all_selected.append(item_selected)
            card_choices.remove(item_selected)
        return tuple(all_selected)


    def interp_anyfeatures(self) -> CardProp:
        return lambda card: True


    def interp_zonedselectionstrategy(self, node: ZonedSelectionStrategy) -> EvaluatedZonedSelectionStrategy:
        num = node.num.interp(self)
        sel = node.selection_lambda.interp(self)
        pid, field = node.src.interp(self)
        return EvaluatedZonedSelectionStrategy(num, sel, pid, field)


    def interp_lowestsuperlative(self) -> Callable[[List[T]], T]:
        return lambda xs: min(xs)
    

    def interp_youexpr(self) -> int:
        return self.you_id
    

    def interp_abstractzoneliteral(self, node) -> PlayerField:
        return node.field
    

    def interp_playerzoneexpr(self, node) -> Tuple[PlayerId, PlayerField]:
        # TODO: restructure PlayerStates to streamline this
        player_id: int = node.player.interp(self)
        zone: PlayerField = node.zone.interp(self)
        return (player_id, zone)
        

    def interp_nocondition(self) -> bool:
        return True
    

    def interp_thoseonesexpr(self) -> List[T]:
        return self.antecedent


    def interp_numberliteralexpr(self, node: NumberLiteralExpr) -> int:
        return node.number
    

    def interp_iconliteralexpr(self, node: IconLiteralExpr) -> Icon:
        return node.icon
    

    def interp_anyquantifier(self) -> Callable[[List[T]], bool]:
        return any
    

    def interp_allquantifier(self) -> Callable[[List[T]], bool]:
        return all
    

    def interp_nonequantifier(self) -> Callable[[List[T]], bool]:
        return lambda xs: not any(xs)
    
    
    def interp_drawandstmt(self, node: DrawAndStmt):
        you = self.you_id
        age: Age = node.age.interp(self)
        amount: int = node.amount.interp(self)
        then: DrawAndFriendlyStmtName = node.then

        new_antecedent = []
        for _ in range(amount):
            # (we have to do these one at a time)
            drawn = self.game.draw(you, age, 1)[0]
            new_antecedent.append(drawn)
            # TODO: expand stub
            if then == DrawAndFriendlyStmtName.REVEAL:
                self.game.reveal(card_ids=[drawn], owner=self.you_id)
            else:
                raise Exception(f"Unimplemented: {then}")
        
        self.antecedent = new_antecedent
        if then == DrawAndFriendlyStmtName.REVEAL:
            self.antecedent_zones = [(self.you_id, PlayerField.HAND)]
        elif then == DrawAndFriendlyStmtName.SCORE:
            self.antecedent_zones = [(self.you_id, PlayerField.SCORE_PILE)]


    def interp_stmts(self, node: Stmts):
        for stmt in node:
            self.interp_stmt(stmt)


    def interp_repeatstmt(self):
        self.interp_stmts(self.this_effect.effects)