import json
import time
import paho.mqtt.client as mqtt
from random import Random
from threading import Event
from minigames import Minigame
from Player import Player
from Utils import Utils, LCDMessage

BUTTON_TOPIC = "game/players/{id}/components/button"

class LastStickStanding(Minigame):
    """
    Last Stick Standing:
    Players take turns removing sticks from a pile. The player who removes the last stick loses.
    """

    def __init__(self, players: list[Player], client: mqtt.Client) -> None:
        super().__init__(players, client)
        self.sticks = 12
        self.lastStickStandingEvent = Event()
        self.current_player_index = 0
        self.sticks_to_take = 1

    def playGame(self) -> list[Player]:
        self.utils.printDebug(f"Starting game with {self.sticks} sticks")
        self.introduceGame()
        self.client.subscribe(BUTTON_TOPIC.format(id="+"))
        self.showTurnInfo()
        self.lastStickStandingEvent.wait()
        self.client.unsubscribe(BUTTON_TOPIC.format(id="+"))
        time.sleep(2)
        winners = [player for player in self.players if player.id != self.last_player]
        return winners  # Return winners directly without additional filtering
    
    def handleMQTTMessage(self, message: mqtt.MQTTMessage) -> None:
        player_id = int(message.topic.split("/")[2])
        if message.topic == BUTTON_TOPIC.format(id=player_id) and player_id == self.players[self.current_player_index].id:
            payload = json.loads(message.payload.decode("utf-8"))
            press_type = payload["type"]
            self.utils.printDebug(payload)
            if press_type == "short":
                self.toggleSticksToTake()
            elif press_type == "long":
                self.removeStick(player_id)

    def showTurnInfo(self) -> None:
        current_player = self.players[self.current_player_index]
        sticks_visual = "|" * self.sticks + f"{self.sticks:>2}".rjust(16 - self.sticks)
        self.utils.printDebug(f"Turn: Player {current_player.id} - Sticks remaining: {self.sticks}")
        
        # Show turn info to current player
        self.utils.showInLCD(
            current_player.id, 
            LCDMessage(
                top=f"Take: {self.sticks_to_take} sticks",
                down=sticks_visual
            )
        )
        
        # Show wait info to other players
        self.utils.showInOtherLCD(
            current_player.id, 
            LCDMessage(
                top=f"Wait for P{current_player.id}",
                down=sticks_visual
            )
        )

    def toggleSticksToTake(self) -> None:
        if self.sticks > 2:  # Changed from >= to >
            self.sticks_to_take = 2 if self.sticks_to_take == 1 else 1
            self.utils.printDebug(f"Player {self.players[self.current_player_index].id} selected to take {self.sticks_to_take} sticks")
        else:
            self.sticks_to_take = 1
            self.utils.printDebug("Only 1 stick can be taken")
        self.showTurnInfo()

    def removeStick(self, player_id: int) -> None:
        self.utils.printDebug(f"Player {player_id} removes {self.sticks_to_take} sticks")
        self.sticks -= self.sticks_to_take
        
        if self.sticks > 0:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            self.sticks_to_take = 1
            self.showTurnInfo()
        else:
            self.last_player = player_id
            self.utils.printDebug(f"Game Over - Player {player_id} loses!")
            self.lastStickStandingEvent.set()


    def introduceGame(self) -> None:
        self.utils.showInAllLCD(LCDMessage(top="Last Stick".center(16), down="Standing".center(16)))
        time.sleep(3)
        self.utils.showInAllLCD(LCDMessage(top="If you take", down="the last stick"))
        time.sleep(3)
        self.utils.showInAllLCD(LCDMessage(top="You lose!".center(16)))
        time.sleep(3)
        self.utils.showInAllLCD(LCDMessage(top="Short:", down="Take 1-2 sticks"))
        time.sleep(3)
        self.utils.showInAllLCD(LCDMessage(top="Long:", down="Confirm"))
        time.sleep(3)
        self.startCountdown()
        time.sleep(1)