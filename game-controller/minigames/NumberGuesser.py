import json
import time
import paho.mqtt.client as mqtt
from random import Random
from threading import Event
from minigames import Minigame
from Player import Player
from Utils import Utils, LCDMessage
from Melodies import NUMBER_GUESSER_TUNE  # Add this import at the top


BUTTON_TOPIC = "game/players/{id}/components/button"

class NumberGuesser(Minigame):
    """
    Number Guesser: Guess a hidden target number without going over.
    - Rules: 
        - Players have to guess a number between a specified range, without knowing the control base’s hidden number. 
        - The player with the closest guess, without exceeding the target, wins the round.
        - It's reminiscent of the classic "The Price is Right" game ("Precio Justo" in Spanish).
    """

    def __init__(self, players: list[Player], client: mqtt.Client, debug: bool) -> None:
        super().__init__(players, client, debug)
        self.choices = {player.id: {"finished": False, "choice": 1} for player in self.players}
        self.minGuess, self.maxGuess = 1, 5
        self.number = Random().randint(self.minGuess, self.maxGuess)
        self.numberGuesserEvent = Event()

    def introduceGame(self):
        """
        Displays game introduction and instructions to players.
        Explains number range and button controls.
        
        Returns:
            None
        """
        self.utils.playInAllBuzzer(NUMBER_GUESSER_TUNE)
        self.utils.showInAllLCD(LCDMessage(top="Number Guesser!".center(16)))
        time.sleep(3)
        self.utils.showInAllLCD(LCDMessage(top="Guess the number", down=f"between {self.minGuess} and {self.maxGuess}"))
        time.sleep(3)
        self.utils.showInAllLCD(LCDMessage(top="Short: Change", down="Long: Confirm"))
        time.sleep(3)
        self.startCountdown()
        time.sleep(1)
        self.utils.showInAllLCD(LCDMessage(top="Current number".center(16), down="-> 1 <-".center(16)))

    def playGame(self) -> list[Player]:
        """
        Main game loop for Number Guesser minigame.
        Players try to guess a hidden number without going over.
        
        Returns:
            list[Player]: List of players who guessed closest without exceeding
        """
        self.utils.printDebug(f"The chosen number is: {self.number}")
        self.introduceGame()
        self.client.subscribe(BUTTON_TOPIC.format(id="+"))
        self.numberGuesserEvent.wait()
        self.client.unsubscribe(BUTTON_TOPIC.format(id="+"))
        time.sleep(2)
        self.utils.showInAllLCD(LCDMessage(top="All players".center(16), down="have finished".center(16)))
        time.sleep(3)

        # Show the number
        self.utils.showInAllLCD(LCDMessage(top="The number was".center(16), down=f"{self.number}".center(16)))
        time.sleep(3)
        
        positive_guesses = list(map(lambda value: value["choice"], filter(lambda value: value["choice"] <= self.number, self.choices.values())))
        closest_guess = min(positive_guesses, key=lambda choice: self.number - choice, default=None)
        winners: list[Player] = list(filter(lambda player: self.choices[player.id]["choice"] == closest_guess, self.players))
        return winners

    def handleMQTTMessage(self, message: mqtt.MQTTMessage) -> None:
        """
        Processes button presses for number selection.
        Short press increments number, long press confirms selection.
        
        Args:
            message: MQTT message containing button press information
            
        Returns:
            None
        """
        player_id = int(message.topic.split("/")[2])
        if message.topic == BUTTON_TOPIC.format(id=player_id):
            payload = json.loads(message.payload.decode("utf-8"))
            press_type = payload["type"]
            self.utils.printDebug(payload)
            if press_type == "short" and self.choices[player_id]["finished"] == False:
                current_choice = self.choices[player_id]["choice"]
                new_choice = current_choice + 1 if current_choice < self.maxGuess else self.minGuess
                self.choices[player_id]["choice"] = new_choice
                self.utils.showInLCD(
                    player_id, LCDMessage(top="Current number".center(16), down=f"-> {new_choice} <-".center(16))
                )
            elif press_type == "long":
                choice = self.choices[player_id]["choice"]
                self.choices[player_id]["finished"] = True
                top = f"Number {choice} chosen".center(16)
                # Check if all players have finished
                if all(choice["finished"] for choice in self.choices.values()):
                    down = ""
                    self.numberGuesserEvent.set()
                else:
                    down = "Wait for others"
                self.utils.showInLCD(player_id, LCDMessage(top=top, down=down))
