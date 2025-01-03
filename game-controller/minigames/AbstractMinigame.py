
from abc import ABC, abstractmethod
from paho.mqtt.client import mqtt
from Player import Player

general_minigame_topic = "game/minigame"
minigame_topic = "game/minigame/{game_id}"

class Minigame(ABC):
    def __init__(self, players: Player, client: mqtt.Client) -> None:
        self.players = players
        self.client = client
        self.minigame_topic = minigame_topic
    
    @abstractmethod
    def startGame(self) -> None:
        pass
    
    @abstractmethod
    def handleMQTTMessage(self, message: str) -> None:
        pass