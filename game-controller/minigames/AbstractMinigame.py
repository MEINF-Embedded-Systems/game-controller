
from abc import ABC, abstractmethod
import paho.mqtt.client as mqtt
from Player import Player

general_minigame_topic = "game/minigame"
minigame_topic = "game/minigame/{game_id}"

class Minigame(ABC):
    def __init__(self, players: list[Player], client: mqtt.Client) -> None:
        self.players = players
        self.client = client
        self.minigame_topic = minigame_topic
    
    @abstractmethod
    def playGame(self) -> list[Player]:
        pass
    
    @abstractmethod
    def handleMQTTMessage(self, message: str) -> None:
        pass
    
    @abstractmethod
    def introduceGame(self) -> None:
        pass