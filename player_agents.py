from abc import ABC, abstractmethod
from game_state import Card

# PlayerAgents are what make decisions.
class PlayerAgent(ABC):
    @abstractmethod
    def choose_meld_from_hand(self) -> Card:
        ...