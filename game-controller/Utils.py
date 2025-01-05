from Message import LCDMessage, BuzzerMessage
from colorama import Fore

PLAYERS_LCD_TOPIC = "game/players/{id}/components/lcd"
PLAYERS_BUZZER_TOPIC = "game/players/{id}/components/buzzer"


class Utils:
    def __init__(self, client, players, debug=True) -> None:
        self.client = client
        self.players = players
        self.debug = debug

    def printDebug(self, message: str) -> None:
        if self.debug:
            print(Fore.YELLOW + f"DEBUG: {message}" + Fore.RESET)

    def showInLCD(self, player_id, message: LCDMessage) -> None:
        topic = PLAYERS_LCD_TOPIC.format(id=player_id)
        payload = message.toJson()
        self.client.publish(topic, payload)
        self.printDebug(f"(Player {player_id} LCD) {message}")

    def showInOtherLCD(self, player_id, message: LCDMessage) -> None:
        for other in self.players:
            if other.id != player_id:
                self.showInLCD(other.id, message)

    def showInAllLCD(self, message: LCDMessage) -> None:
        for player in self.players:
            self.showInLCD(player.id, message)

    def playInBuzzer(self, player_id, message: BuzzerMessage) -> None:
        topic = PLAYERS_BUZZER_TOPIC.format(id=player_id)
        payload = message.toJson()
        self.client.publish(topic, payload)
        self.printDebug(f"(Player {player_id} Buzzer) {message}")

    def playInOtherBuzzer(self, player_id, message: BuzzerMessage) -> None:
        for other in self.players:
            if other.id != player_id:
                self.playInBuzzer(other.id, message)

    def playInAllBuzzer(self, message: BuzzerMessage) -> None:
        for player in self.players:
            self.playInBuzzer(player.id, message)
