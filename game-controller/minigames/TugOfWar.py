import json
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
    Tug of War:
    - Objective: Pull the virtual rope onto your screen.
    - Rules: Players repeatedly press the button to move a virtual rope closer to their side on the control base LCD screen. The first player to pull the rope past a threshold wins.
    It's reminiscent of the classic "Tug of War" game ("Tira y Afloja" in Spanish).
    """

    def __init__(self, players: list[Player], client: mqtt.Client) -> None:
        super().__init__(players, client)
        self.hits = {player.id: 0 for player in self.players}
        self.utils = Utils(client, players, debug=True)
        self.tugOfWarEvent = Event()

    def introduceGame(self):
        self.utils.showInAllLCD(LCDMessage(top="Tug of War".center(16)))
        time.sleep(3)
        self.utils.showInAllLCD(LCDMessage(top="Pull the rope".center(16), down="to your side".center(16)))
        time.sleep(3)
        self.utils.showInAllLCD(LCDMessage(top="Short: Pull the", down="rope"))
        time.sleep(3)
        sequence = [3, 2, 1, "GO!"]
        for elem in sequence:
            self.utils.showInAllLCD(LCDMessage(top="Ready?".center(16), down=str(elem).center(16)))    
            time.sleep(1)
        time.sleep(1)
        self.utils.showInAllLCD(LCDMessage(top="Tug of War".center(16), down="-" * 16))


    def playGame(self) -> list[Player]:
        self.introduceGame()
        self.client.subscribe(BUTTON_TOPIC.format(id="+"))
        self.tugOfWarEvent.wait()
        self.client.unsubscribe(BUTTON_TOPIC.format(id="+"))
        time.sleep(2)
        self.utils.showInAllLCD(LCDMessage(top="Finished!"))
        time.sleep(3)
        winner = max(self.hits.keys(), key=lambda id: self.hits[id])
        return [player for player in self.players if player.id == winner]

    def handleMQTTMessage(self, message: mqtt.MQTTMessage) -> None:
        player_id = int(message.topic.split("/")[2])
        if message.topic == BUTTON_TOPIC.format(id=player_id):
            try:
                print(message.payload)
                payload = json.loads(message.payload.decode("utf-8"))
                self.utils.printDebug(payload)

                self.hits[player_id] += 1
                # Get player ids sorted
                sorted_players = sorted(self.hits.keys())

                rope = None

                player_1_id = sorted_players[0]
                player_2_id = sorted_players[1]

                player_1_hits = self.hits[player_1_id]
                player_2_hits = self.hits[player_2_id]

                difference = abs(player_1_hits - player_2_hits)

                if player_1_hits > player_2_hits:
                    rope = "-" * (16 - difference) + " " * difference
                elif player_1_hits < player_2_hits:
                    rope = " " * difference + "-" * (16 - difference)
                else:
                    rope = "-" * 16

                self.utils.showInAllLCD(LCDMessage(top="Tug of War".center(16), down=rope))

                if difference >= 16:
                    self.tugOfWarEvent.set()
            except Exception as e:
                pass
