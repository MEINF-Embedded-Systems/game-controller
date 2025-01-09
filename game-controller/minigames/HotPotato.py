from minigames import Minigame
from Player import Player
import paho.mqtt.client as mqtt
import time
from Message import LCDMessage, BuzzerMessage
from Utils import Utils
from threading import Event, Timer
import json
import random

# MQTT Topics
BUTTON_TOPIC = "game/players/{id}/components/button"

class HotPotato(Minigame):
    """
    Hot Potato: Players pass a virtual "potato" by pressing a button.
    The player holding the "potato" when the timer expires loses.
    """

    def __init__(self, players: list[Player], client: mqtt.Client) -> None:
        super().__init__(players, client)
        self.current_player = random.choice(players)
        self.timer_duration = random.randint(10, 30)
        self.utils = Utils(client, players, debug=True)
        self.hot_potato_event = Event()
        self.explosion_timer = None
        self.beep_timer = None
        self.last_beep_time = 0

    def playGame(self) -> list[Player]:
        self.startGameDebugInfo()
        self.introduceGame()
        self.startCountdown()

        self.start_time = time.time()
        self.client.subscribe(BUTTON_TOPIC.format(id="+"))

        # Display the current player holding the potato
        self.displayPotatoHolder()

        # Start the timer for the explosion
        self.explosion_timer = Timer(self.timer_duration, self.explodePotato)
        self.explosion_timer.start()

        # Start the beeping sequence
        self.scheduleBeep()

        # Wait for the game end
        self.hot_potato_event.wait()

        self.client.unsubscribe(BUTTON_TOPIC.format(id="+"))

        loser = self.current_player
        winners = [player for player in self.players if player != loser]

        return winners

    def startGameDebugInfo(self):
        self.utils.printDebug("Starting Hot Potato minigame")
        self.utils.printDebug(f"Timer duration: {self.timer_duration}")
        self.utils.printDebug(f"Starting player: {self.current_player.id}")

    def introduceGame(self):
        self.utils.showInAllLCD(LCDMessage(top="Hot Potato!".center(16)))
        time.sleep(3)
        self.utils.showInAllLCD(LCDMessage(top="Press button to", down="pass the potato!"))
        time.sleep(3)
        self.utils.showInAllLCD(LCDMessage(top="Pass it quickly!", down="It's hot!"))
        time.sleep(3)
        self.utils.showInAllLCD(LCDMessage(top="Avoid holding it", down="when it blows!"))
        time.sleep(3)

    def handleMQTTMessage(self, message: mqtt.MQTTMessage):
        if not self.hot_potato_event.is_set():  # Ignore button presses after the game ends
            player_id = int(message.topic.split("/")[2])
            if message.topic == BUTTON_TOPIC.format(id=player_id) and self.current_player.id == player_id:
                self.passPotato()
                self.displayPotatoHolder()  

    def passPotato(self):
        # Update the current player
        current_player_index = self.players.index(self.current_player)
        next_player_index = (current_player_index + 1) % len(self.players)
        self.current_player = self.players[next_player_index]
        self.utils.printDebug(f"Potato passed to Player {self.current_player.id}")
        # Pass sound
        self.utils.beepPlayer(self.current_player.id, duration_ms=100, frequency=500)

    def explodePotato(self):
        # Set the event to stop the game
        self.hot_potato_event.set() 
        self.utils.printDebug("BOOM! The potato exploded!")

        # Cancel the explosion timer
        if self.beep_timer:
            self.beep_timer.cancel()

        # Explosion sound and message
        self.utils.beepAllPlayers(duration_ms=2000, frequency=100)
        self.utils.showInAllLCD(LCDMessage(top="BOOM!".center(16), down="Potato exploded!"))
        time.sleep(3)

    def scheduleBeep(self):
        remaining_time = max(0, self.timer_duration - (time.time() - self.start_time))  # Prevent negative time
        beep_interval = remaining_time / 10 + 0.1  # Faster beeps, adjusted formula

        if remaining_time > 0:
            if time.time() - self.last_beep_time >= beep_interval:
                self.utils.playInAllBuzzer(BuzzerMessage(tones=[1000, 0], duration=[100, 0]))
                self.last_beep_time = time.time()  # Update last beep time inside the 'if'

            self.beep_timer = Timer(0.1, self.scheduleBeep)
            self.beep_timer.start()

    def displayPotatoHolder(self):
        """Update the LCDs to show who has the potato"""
        self.utils.showInLCD(
            self.current_player.id,
            LCDMessage(top="You have", down="the potato!"),
        )
        self.utils.showInOtherLCD(
            self.current_player.id,
            LCDMessage(top=f"Player {self.current_player.id} has", down="the potato!"),
        )
