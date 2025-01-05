import json
import time
import paho.mqtt.client as mqtt
from random import Random
from threading import Event
from minigames import Minigame
from Player import Player
from Utils import Utils, LCDMessage


BUTTON_TOPIC = "game/players/{id}/components/button"


class NumberGuesser(Minigame):
    """
    Number Guesser:
    Players have to guess a number between a specified range, without knowing the control base’s hidden number.
    The player with the closest guess, without exceeding the target, wins the round.
    """

    def __init__(self, players: list[Player], client: mqtt.Client) -> None:
        super().__init__(players, client)
        self.choices = {player.id: {"finished": False, "choice": 1} for player in self.players}
        self.number = None
        self.minGuess, self.maxGuess = 1, 5
        self.utils = Utils(client, players, debug=True)
        self.numberGuesserEvent = Event()

    def playGame(self) -> list[Player]:
        self.number = Random().randint(self.minGuess, self.maxGuess)
        self.utils.printDebug(f"Number to guess: {self.number}")
        self.introduceGame()
        self.client.subscribe(BUTTON_TOPIC.format(id="+"))
        self.numberGuesserEvent.wait()
        self.client.unsubscribe(BUTTON_TOPIC.format(id="+"))
        positive_guesses = [
            self.choices[player_id]["choice"]
            for player_id in self.choices
            if self.choices[player_id]["choice"] <= self.number
        ]
        closest_guess = min(positive_guesses, key=lambda choice: self.number - choice, default=None)
        winners = [player for player in self.players if self.choices[player.id]["choice"] == closest_guess]
        return winners

    def handleMQTTMessage(self, message: mqtt.MQTTMessage) -> None:
        player_id = int(message.topic.split("/")[2])
        if message.topic == BUTTON_TOPIC.format(id=player_id):
            payload = json.loads(message.payload.decode("utf-8"))
            press_type = payload["type"]
            print(payload)
            if press_type == "short" and self.choices[player_id]["finished"] == False:
                current_choice = self.choices[player_id]["choice"]
                new_choice = current_choice + 1 if current_choice < self.maxGuess else self.minGuess
                self.choices[player_id]["choice"] = new_choice
                self.utils.showInLCD(
                    player_id, LCDMessage(top="Current number".center(16), down=f"-> {new_choice} <-".center(16))
                )
            elif press_type == "long":
                self.choices[player_id]["finished"] = True
                self.utils.showInLCD(player_id, LCDMessage(top="Number confirmed", down="Wait for others"))
                # Check if all players have finished
                if all(choice["finished"] for choice in self.choices.values()):
                    self.numberGuesserEvent.set()

    def introduceGame(self):
        self.utils.showInAllLCD(LCDMessage(top="Number Guesser".center(16)))
        time.sleep(3)
        self.utils.showInAllLCD(LCDMessage(top="Guess the number", down=f"between {self.minGuess} and {self.maxGuess}"))
        time.sleep(3)
        self.utils.showInAllLCD(LCDMessage(top="Short: Change", down="Long: Confirm"))
        time.sleep(3)
        self.utils.showInAllLCD(LCDMessage(top="Current number".center(16), down="-> 1 <-".center(16)))
