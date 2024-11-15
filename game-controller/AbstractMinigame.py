
from abc import ABC, abstractmethod

class Minigame(ABC):
    def __init__(self, num_players: int) -> None:
        self.num_players = num_players
    
    
    @abstractmethod
    def handleMQTTMessage(self, message: str) -> None:
        pass