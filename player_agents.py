from abc import ABC, abstractmethod
from game_state import Card, GameState
from typing import List, Tuple

# PlayerAgents are what make decisions.
# TODO: an abstract base class here will be nice for debugging...
class PlayerAgent(ABC):
    # @abstractmethod
    # def choose_meld_from_hand(self) -> Card:
    #     ...
    
    @abstractmethod
    def choose_turn_action(self) -> Tuple[str, List[str]]:
        ...


class ScriptedAgent(PlayerAgent):
    def __init__(self, script : List[str]):
        self.script = script
        self.action_num = 0
    
    def choose_turn_action(self) -> Tuple[str, List[str]]:
        if self.action_num >= len(self.script):
            raise Exception("Out of commands")
        # just do the next thing in the script
        next_command = self.script[self.action_num].split(' ')
        cmd_type = next_command[0]
        cmd_args = next_command[1:]
        self.action_num += 1
        return cmd_type, cmd_args