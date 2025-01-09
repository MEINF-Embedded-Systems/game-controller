import json
from json import JSONDecodeError
import time
import paho.mqtt.client as mqtt
from random import Random
from threading import Event
from minigames import Minigame
from Player import Player
from Utils import Utils, LCDMessage


BUTTON_TOPIC = "game/players/{id}/components/button"


class TugOfWar(Minigame):
    """
    Tug of War: Pull the virtual rope onto your screen.
    - Rules: 
        - Players repeatedly press the button to move a virtual rope closer to their side on the control base LCD screen. 
        - The first player to pull the rope past a threshold wins.
        - It's reminiscent of the classic "Tug of War" game ("Tira y Afloja" in Spanish).
    """

    def __init__(self, players: list[Player], client: mqtt.Client) -> None:
        super().__init__(players, client)
        self.hits = 0
        self.tugOfWarEvent = Event()

    def introduceGame(self):
        self.utils.showInAllLCD(LCDMessage(top="Tug of War".center(16)))
        time.sleep(3)
        self.utils.showInAllLCD(LCDMessage(top="Pull the rope".center(16), down="to your side".center(16)))
        time.sleep(3)
        self.utils.showInAllLCD(LCDMessage(top="Long: Pull the", down="rope"))
        time.sleep(3)
        self.startCountdown()
        time.sleep(1)
        self.utils.showInAllLCD(LCDMessage(top="P1-Tug of War-P2".center(16), down="-" * 16))

    def playGame(self) -> list[Player]:
        self.introduceGame()
        self.client.subscribe(BUTTON_TOPIC.format(id="+"))
        self.tugOfWarEvent.wait()
        self.client.unsubscribe(BUTTON_TOPIC.format(id="+"))
        time.sleep(2)
        self.utils.showInAllLCD(LCDMessage(top="Tug of War".center(16), down="finished!".center(16)))
        time.sleep(3)
        winner: Player = self.players[0] if self.hits < 0 else self.players[1]
        return [winner]

    def handleMQTTMessage(self, message: mqtt.MQTTMessage) -> None:
        player_id = int(message.topic.split("/")[2])
        if message.topic == BUTTON_TOPIC.format(id=player_id):
            try:
                payload = json.loads(message.payload.decode('utf-8'))
                if payload["type"] == "long" and not self.tugOfWarEvent.is_set():
                    self.utils.beepPlayer(player_id, frequency=500)
                    player_1, player_2 = self.players
                    if player_id == player_1.id:
                        self.hits -= 3
                    elif player_id == player_2.id:
                        self.hits += 3
                    rope = self.getRope()
                    self.utils.showInAllLCD(LCDMessage(top="P1-Tug of War-P2".center(16), down=rope))
                    
                    if abs(self.hits) >= 16:
                        self.tugOfWarEvent.set()
            except JSONDecodeError:
                pass

    def getRope(self):
        rope = None
        if self.hits < 0:
            hits = abs(self.hits)
            rope = "-" * (16 - hits) + " " * (hits)
        elif self.hits > 0:
            rope = " " * (self.hits) + "-" * (16 - self.hits)
        else:
            rope = "-" * 16
        return rope
