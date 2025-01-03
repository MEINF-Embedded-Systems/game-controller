from random import Random
from threading import Event
from AbstractMinigame import Minigame
import paho.mqtt.client as mqtt

general_minigame_topic = "game-controller/minigame"
topic = general_minigame_topic + "/number-guesser/player/{player_id}/choice"

numberGuesserEvent = Event()

class NumberGuesser(Minigame):
    def __init__(self) -> None:
        super().__init__()
        self.choices = {}
        self.minigame_topic = self.minigame_topic.format(game_id="number-guesser")
        self.number = None

    def playGame(self) -> None:
        minGuess, maxGuess = 1, 5
        self.number = Random().randint(minGuess, maxGuess)
        numberGuesserEvent.wait()
        winner = min(self.choices, key=lambda player_id: self.number - self.choices[player_id])
        winner.gainPoints(15)

    def handleMQTTMessage(self, message: mqtt.MQTTMessage) -> None:
        player_id = message.topic.split("/")[4]
        if message.topic == topic.format(player_id=player_id):
            self.choices[player_id] = int(message.payload)
            if len(self.choices) == self.num_players:
                numberGuesserEvent.set()
