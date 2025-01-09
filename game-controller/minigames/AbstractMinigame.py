
from abc import ABC, abstractmethod
import time
import paho.mqtt.client as mqtt
from Player import Player
from Utils import Utils, LCDMessage, BuzzerMessage


general_minigame_topic = "game/minigame"
minigame_topic = "game/minigame/{game_id}"

class Minigame(ABC):
    def __init__(self, players: list[Player], client: mqtt.Client) -> None:
        self.players = players
        self.client = client
        self.utils = Utils(client, players, debug=True)
    
    @abstractmethod
    def playGame(self) -> list[Player]:
        pass
    
    @abstractmethod
    def handleMQTTMessage(self, message: str) -> None:
        pass
    
    @abstractmethod
    def introduceGame(self) -> None:
        pass
    
    def startCountdown(self):
        for elem in [3, 2, 1, "GO!"]:
            self.utils.showInAllLCD(LCDMessage(top="Ready?".center(16), down=str(elem).center(16)))
            time.sleep(1)