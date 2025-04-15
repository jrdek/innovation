
from player_agents import PlayerAgent
from typing import List, Tuple
from structs import T, GameState, CardId


class AgentLiaison:
    def __init__(self, agents: List[PlayerAgent]):
        self.agents = agents


    def request_choice_of_many(self, current_state: GameState, pid: int, bank: List[T], how_many: int) -> Tuple[str, List[T]]:
        if len(bank) == 0:
            return []
        chosen = self.agents[pid].choose(
            state=current_state,
            bank=bank,
            how_many=how_many
        )
        assert len(chosen) == how_many
        assert all(item in bank for item in chosen)
        return self.agents[pid].name, chosen
    

    def request_choice_of_one(self, current_state: GameState, pid: int, bank: List[T]) -> T:
        name, chosen = self.request_choice_of_many(current_state, pid, bank, 1)
        if len(chosen) == 0:
            return None
        return name, chosen[0]
    

    def reveal_cards(self, current_state: GameState, card_ids: List[CardId], owner: int):
        for i, agent in enumerate(self.agents):
            if i != owner:
                agent.notify(state=current_state, card_ids=card_ids, owner=owner)