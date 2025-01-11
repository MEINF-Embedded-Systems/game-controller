from minigames import Minigame
from Player import Player
import paho.mqtt.client as mqtt
import time
from Message import LCDMessage, BuzzerMessage
from Utils import Utils
from threading import Event, Timer
import json
import random
from Melodies import HOT_POTATO_TUNE  # Add this import at the top

# MQTT Topics
BUTTON_TOPIC = "game/players/{id}/components/button"

class HotPotato(Minigame):
    """
    Hot Potato: Players pass a virtual "potato" by pressing a button.
    The player holding the "potato" when the timer expires loses.
    """

    def __init__(self, players: list[Player], client: mqtt.Client, debug: bool) -> None:
        super().__init__(players, client, debug)
        self.current_player = random.choice(players)
        self.timer_duration = random.randint(10, 30)
        self.hot_potato_event = Event()
        self.explosion_timer = None
        self.beep_timer = None
        self.last_beep_time = 0

    def playGame(self) -> list[Player]:
        """
        Main game loop for Hot Potato minigame.
        Manages timer, potato passing, and winner determination.
        
        Returns:
            list[Player]: List of players who weren't holding the potato when it exploded
        """
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
        """
        Prints debug information about game configuration.
        Displays timer duration and starting player.
        
        Returns:
            None
        """
        self.utils.printDebug("Starting Hot Potato minigame")
        self.utils.printDebug(f"Timer duration: {self.timer_duration}")
        self.utils.printDebug(f"Starting player: {self.current_player.id}")

    def introduceGame(self):
        """
        Displays game introduction and instructions to players.
        Explains hot potato mechanics and passing rules.
        
        Returns:
            None
        """
        self.utils.playInAllBuzzer(HOT_POTATO_TUNE)
        self.utils.showInAllLCD(LCDMessage(top="Hot Potato!".center(16)))
        time.sleep(3)
        self.utils.showInAllLCD(LCDMessage(top="Press button to".center(16), down="pass the potato!".center(16)))
        time.sleep(3)
        self.utils.showInAllLCD(LCDMessage(top="Pass it quickly!".center(16), down="It's hot!".center(16)))
        time.sleep(3)
        self.utils.showInAllLCD(LCDMessage(top="Avoid holding it".center(16), down="when it blows!".center(16)))
        time.sleep(3)

    def handleMQTTMessage(self, message: mqtt.MQTTMessage):
        """
        Processes button presses for potato passing.
        Validates current holder before allowing pass.
        
        Args:
            message: MQTT message containing button press
            
        Returns:
            None
        """
        if not self.hot_potato_event.is_set():  # Ignore button presses after the game ends
            player_id = int(message.topic.split("/")[2])
            if message.topic == BUTTON_TOPIC.format(id=player_id) and self.current_player.id == player_id:
                self.passPotato()
                self.displayPotatoHolder()  

    def passPotato(self):
        """
        Handles passing the potato to the next player.
        Updates current holder and provides feedback.
        
        Returns:
            None
        """
        # Update the current player
        current_player_index = self.players.index(self.current_player)
        next_player_index = (current_player_index + 1) % len(self.players)
        self.current_player = self.players[next_player_index]
        self.utils.printDebug(f"Potato passed to Player {self.current_player.id}")

        # Sound effect to notify new potato holder
        self.utils.beepPlayer(self.current_player.id, duration_ms=200, frequency=500)

    def explodePotato(self):
        """
        Handles end of game when timer expires.
        Triggers explosion effects and stops game.
        
        Returns:
            None
        """
        # Set the event to stop the game
        self.hot_potato_event.set() 
        self.utils.printDebug("BOOM! The potato exploded!")

        # Cancel the explosion timer
        if self.beep_timer:
            self.beep_timer.cancel()

        # Explosion sound and message
        self.utils.beepAllPlayers(duration_ms=2000, frequency=100)
        self.utils.showInAllLCD(LCDMessage(top="BOOM!".center(16), down="Potato exploded!".center(16)))
        time.sleep(3)

    def scheduleBeep(self):
        """
        Manages warning beeps that increase in frequency.
        Beep interval decreases as timer runs down.
        
        Returns:
            None
        """
        time_elapsed = time.time() - self.start_time
        remaining_time = max(0, self.timer_duration - time_elapsed) # Prevent negative values

        initial_beep_rate = 1.5  # Initial beep interval in seconds
        acceleration_factor = remaining_time / self.timer_duration 
        beep_interval = initial_beep_rate * acceleration_factor + 0.1  # Decrease the interval as the time decreases

        if remaining_time > 0:
            if time.time() - self.last_beep_time >= beep_interval:
                self.utils.playInAllBuzzer(BuzzerMessage(tones=[1000, 0], duration=[100, 0]))
                self.last_beep_time = time.time()  

            # Continue scheduling the next beep
            self.beep_timer = Timer(0.1, self.scheduleBeep)
            self.beep_timer.start()


    def displayPotatoHolder(self):
        """
        Updates LCD displays to show current potato holder.
        Shows different messages to holder and other players.
        
        Returns:
            None
        """
        self.utils.showInLCD(
            self.current_player.id,
            LCDMessage(top="You have".center(16), down="the potato!".center(16)),
        )
        self.utils.showInOtherLCD(
            self.current_player.id,
            LCDMessage(top=f"Player {self.current_player.id} has".center(16), down="the potato!".center(16)),
        )
