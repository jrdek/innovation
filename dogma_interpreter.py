from dogma_ir_typing import *
from structs import *
from typing import List, Tuple
from gameplay import draw_n, meld_from_hand, do_turn_draw, score_card_from_pid_field
from agent_liaison import AgentLiaison

# TODO: fix GameStateTransition for returning cards...

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
        return self.state.players[self.you_id].name
    
    def me(self) -> str:
        return self.state.players[self.me_id].name
    
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
        return [node.strat.src.interp()] * len(node.interp())
        
    

    def get_loc(self, pid: PlayerId, field: PlayerField) -> CardLoc:
        # TODO: handle for quick lookup on board vs in specific piles!
        # also restructure the PlayerState class to make this more ergonomic.
        # in general, this is an unsatisfying structure...
        player = self.state.players[pid]
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


    def interpret_card(self, state: GameState, me_id: int, card: Card):
        self.applied_changes.clear()  # TODO: maybe scrap this for now...
        self.state = state
        self.me_id = me_id
        self.you_id = me_id  # TODO
        self.antecedent.clear()
        self.other_player_acted = False
        for dogma_effect in card.dogmata:
            self.this_effect: DEffect = dogma_effect
            if dogma_effect.is_demand:
                self.interpret_demand_effect(dogma_effect)
            else:
                self.interpret_shared_effect(dogma_effect)


    def interpret_demand_effect(self, deffect: DEffect):
        ...

    
    def interpret_shared_effect(self, deffect: DEffect):
        num_players = len(self.state.players)
        self.you_id = (self.me_id + 1) % num_players
        my_icon_count = self.state.players[self.me_id].count_icon(deffect.key_icon)
        if self.state.debug[DFlags.GAME_LOG]:
            print(f"\tIt's a shared effect. {self.me()} has {my_icon_count} {deffect.key_icon}.")
        for _ in range(num_players):
            your_icon_count = self.state.players[self.you_id].count_icon(deffect.key_icon)
            if your_icon_count >= my_icon_count:
                if self.state.debug[DFlags.GAME_LOG]:
                    if self.you_id != self.me_id:
                        print(f"\t\t{self.you()} has {your_icon_count} {deffect.key_icon}, so it can share.")  # TODO: better pretty-printing here
                    else:
                        print(f"\t\tFinally, {self.me()} uses the effect.")
                for stmt in deffect.effects:
                    self.interp_stmt(stmt)  # do the dogma for that player
                    if self.state.winner is not None:
                        return  # game over, man!
            else:
                if self.state.debug[DFlags.GAME_LOG]:
                    print(f"\t\t{self.you()} has {your_icon_count} {deffect.key_icon}, so it cannot share.")
            self.you_id = (self.you_id + 1) % num_players  # go to the next player
        if self.other_player_acted:
            self.state, card = do_turn_draw(self.state, self.me_id)
            if self.state.debug[DFlags.GAME_LOG]:
                print(f"\tSomeone shared the effect, so {self.me()} takes a turn draw:")
                print(f"\t\t{card}")
        return


    def interp_stmt(self, node: Stmt):
        # split across stmt types. TODO.
        old_state = self.state
        node.interp(self)
        if (self.state != old_state) and self.you_id != self.me_id:
            self.other_player_acted = True
        return
    

    def draw_one(self, age: Age) -> Card:
        you = self.you_id
        new_state, card = draw_n(self.state, you, age)
        if new_state.winner is not None:
            # drew an 11 -- game over!
            return None
        if self.state.debug[DFlags.GAME_LOG]:
                old_age = age
                drawn_str = f"[{old_age}]"
                if age != old_age:
                    drawn_str += f" (--> [{age}])"
                print(f"\t\t\t{self.you()} draws a {drawn_str}:")
                print(f"\t\t\t\t{card}")
        self.state = new_state
        return card

    
    def interp_drawstmt(self, node: DrawStmt):
        amount = node.amount.interp(self)
        age = node.age.interp(self)
        
        new_antecedent = []

        for _ in range(amount):
            card = self.draw_one(age)
            new_antecedent.append(card)

        self.antecedent = new_antecedent
        self.antecedent_zones = [(self.you_id, PlayerField.HAND)] * amount

    
    def interp_scorestmt(self, node: ScoreStmt):
        cards: List[Card] = node.cards.interp(self)
        cards_zones: List[Tuple[PlayerId, PlayerField]] = node.cards.get_zones(self)
        you: int = self.you_id
        
        new_antecedent = []
        
        for card, card_zone in zip(cards, cards_zones):
            owner, field = card_zone
            self.state = score_card_from_pid_field(card, you, owner, field, self.state)
            if self.state.debug[DFlags.GAME_LOG]:
                print(f"\t\t\t{self.you()} scores {card}. (Total score: {self.state.players[you].count_score()})")

        self.antecedent = new_antecedent
        self.antecedent_zones = [(self.you_id, PlayerField.SCORE_PILE)] * len(cards)


    
    # TODO: make an update_antecedent macro
    def interp_meldstmt(self, node: MeldStmt):
        cards = node.cards.interp(self)
        you: int = self.you_id
        new_antecedent = []

        for card in cards:
            new_state, card = meld_from_hand(self.state, you, card)
            if self.state.debug[DFlags.GAME_LOG]:
                print(f"\t\t\t{self.you()} melds {card} from their hand.")
            self.state = new_state
            new_antecedent.append(card)
        
        self.antecedent = new_antecedent
        self.antecedent_zones = self.you_id, PlayerField.BOARD

    
    def interp_ifstmt(self, node: IfStmt):
        condition: bool = node.condition.interp(self)
        if condition:
            node.then_do.interp(self)
        # otherwise nothing


    def interp_cardsarelikeexpr(self, node: CardsAreLikeExpr) -> bool:
        cards: List[Card] = node.cards.interp(self)
        like: CardProp = node.like.interp(self)
        quantifier: Callable[[List[T]], bool] = node.quantifier.interp(self)
        print(f"\t\t\t\t[{', '.join(str(card) + ': ' + str(like(card)) for card in cards)}]")
        return quantifier([like(card) for card in cards])
    

    def interp_hasfeaturefunc(self, node: HasFeatureFunc) -> CardProp:
        # TODO: neaten typing casework
        # also TODO: "if it is purple or yellow"...
        feature = node.feature.interp(self)
        if isinstance(feature, Icon):
            if self.state.debug[DFlags.GAME_LOG]:
                print(f"\t\t\tDoes it have {str(feature)}?")
            return lambda card: feature in card.icons
        raise Exception(f"unimplemented feature type {type(feature)}")


    def interp_cardsthatexpr(self, node: CardsThatExpr) -> List[Card]:
        that : CardProp = node.that.interp(self)
        strat : EvaluatedZonedSelectionStrategy = node.strat.interp(self)
        condition : bool = node.condition.interp(self)  # TODO: what to do with condition?
        
        loc = self.get_loc(strat.pid, strat.field)
        card_choices = [card for card in loc if that(card)]
        all_selected = []
        for _ in range(strat.num):
            item_selected = strat.selection_lambda(card_choices)
            all_selected.append(item_selected)
            card_choices.remove(item_selected)
        return all_selected


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
    

    def reveal(self, cards: List[Card], owner: int):
        self.liaison.reveal_cards(current_state=self.state, cards=cards, owner=owner)
    
    
    def interp_drawandstmt(self, node: DrawAndStmt):
        age = node.age.interp(self)
        amount = node.amount.interp(self)
        then = node.then

        new_antecedent = []
        
        for _ in range(amount):
            drawn = self.draw_one(age)
            new_antecedent.append(drawn)
            # TODO: expand stub
            if then == DrawAndFriendlyStmtName.REVEAL:
                self.reveal(cards=[drawn], owner=self.you_id)
            else:
                raise Exception(f"Unimplemented: {then}")
        
        self.antecedent = new_antecedent
        if then == DrawAndFriendlyStmtName.REVEAL:
            self.antecedent_zones = [(self.you_id, PlayerField.HAND)]
        elif then == DrawAndFriendlyStmtName.SCORE:
            self.antecedent_zones = [(self.you_id, PlayerField.SCORE_PILE)]
        
        # # debug
        # owner, field = self.antecedent_zones[0]
        # print(f"\t\t\t(That action put cards into {self.state.players[owner].name}'s {field.name}.)")


    def interp_stmts(self, node: Stmts):
        for stmt in node:
            self.interp_stmt(stmt)


    def interp_repeatstmt(self):
        self.interp_stmts(self.this_effect.effects)

    
