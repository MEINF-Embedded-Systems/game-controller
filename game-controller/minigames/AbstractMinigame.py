from abc import ABC, abstractmethod
import time
import paho.mqtt.client as mqtt
from Player import Player
from Utils import Utils, LCDMessage

# MQTT topics for minigame communication
general_minigame_topic = "game/minigame"
minigame_topic = "game/minigame/{game_id}"

class Minigame(ABC):
    """
    Abstract base class that defines the interface for all minigames.
    Provides common initialization and utility methods for minigame implementations.
    """
    
    def __init__(self, players: list[Player], client: mqtt.Client, debug: bool) -> None:
        """
        Initialize a new minigame instance.

        Args:
            players: List of players participating in the minigame
            client: MQTT client for communication
            debug: Boolean flag for debug mode

        Returns:
            None
        """
        self.players = players
        self.client = client
        self.utils = Utils(client, players, debug)
    
    @abstractmethod
    def playGame(self) -> list[Player]:
        """
        Execute the main minigame logic.
        Must be implemented by concrete minigame classes.

        Returns:
            list[Player]: List of winning players
        """
        pass
    
    @abstractmethod
    def handleMQTTMessage(self, message: str) -> None:
        """
        Process MQTT messages received during the minigame.
        Must be implemented by concrete minigame classes.

        Args:
            message: MQTT message to process

        Returns:
            None
        """
        pass
    
    @abstractmethod
    def introduceGame(self) -> None:
        """
        Display introduction and instructions for the minigame.
        Must be implemented by concrete minigame classes.

        Returns:
            None
        """
        pass
    
    def startCountdown(self):
        """
        Display a countdown animation before starting the minigame.
        Shows "Ready?" and counts down from 3 to "GO!".

        Returns:
            None
        """
        for elem in [3, 2, 1, "GO!"]:
            self.utils.showInAllLCD(LCDMessage(top="Ready?".center(16), down=str(elem).center(16)))
            time.sleep(1)