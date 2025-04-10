from abc import ABC, abstractmethod
from typing import List, Iterable
from structs import T, TurnAction, Color, Icon, Card, GameState
from enum import Enum

# PlayerAgents are what make decisions.
class PlayerAgent(ABC):
    name: str

    # Given a list of valid options, choose one.
    @abstractmethod
    def choose(self, state: GameState, bank: List[T], num_to_choose: int) -> List[T]:
        ...

    # Update the agent's knowledge of the state of the game (namely, via "reveal" effects).
    @abstractmethod
    def notify(self, state: GameState, cards: List[Card], owner: int):
        ...


class ScriptedAgent(PlayerAgent):
    def __init__(self, name: str, script: str):
        self.name: str = name
        self.script : List[str] = script.split()
        self.choice_num : int = 0
    

    def choose(self, _: GameState, bank: Iterable, how_many: int) -> Iterable[T]:
        assert len(bank) != 0  # (handled elsewhere)
        if self.choice_num >= len(self.script):
            raise Exception("Out of commands")
        
        choices = []
        # just do the next thing in the script
        # interpret that next thing based on the bank's type:
        bank_item = next(iter(bank))
        for _ in range(how_many):
            choice_text = self.script[self.choice_num]
            chosen_object = None
            if isinstance(bank_item, Enum):
                for enum_type in (TurnAction, Color, Icon):
                    if isinstance(bank_item, enum_type):
                        choice_text = choice_text.upper()
                        chosen_object = enum_type[choice_text]
            elif isinstance(bank_item, int):
                chosen_object = int(choice_text)
            elif isinstance(bank_item, Card):
                for card in bank:
                    if card.name == choice_text:
                        chosen_object = card
                if chosen_object is None:
                    raise Exception(f"Couldn't find a card matching \"{choice_text}\" in {[card.name for card in bank]}")
            if chosen_object is None:
                raise Exception(f"Unhandled bank type {type(bank_item)}")
            choices.append(chosen_object)
            self.choice_num += 1
        return choices
    

    def notify(self, state: GameState, cards: List[Card], owner: int):
        # (dummy function; these guys are just following their script)
        print(f"\t\t\t<{self.name}: acknowledging that {state.players[owner].name}'s hand has [{', '.join(str(card) for card in cards)}]>")