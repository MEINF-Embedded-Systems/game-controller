from Message import LCDMessage, BuzzerMessage
from colorama import Fore

# MQTT topic templates for player components
PLAYERS_LCD_TOPIC = "game/players/{id}/components/lcd"
PLAYERS_BUZZER_TOPIC = "game/players/{id}/components/buzzer"

class Utils:
    """
    Utility class for managing player interactions and feedback through LCD and Buzzer components.
    
    Attributes:
        client (mqtt.Client): MQTT client for publishing messages
        players (list[Player]): List of active game players
        debug (bool): Whether to print debug messages
    """

    def __init__(self, client, players, debug=True) -> None:
        """
        Initialize Utils with MQTT client and player list.

        Args:
            client: MQTT client instance for communication
            players: List of Player objects
            debug: Enable/disable debug output (default: True)
        """
        self.client = client
        self.players = players
        self.debug = debug

    def printDebug(self, message: str) -> None:
        """
        Print a debug message if debug mode is enabled.

        Args:
            message: Debug message to print
        """
        if self.debug:
            print(Fore.YELLOW + f"DEBUG: {message}" + Fore.RESET)

    def showInLCD(self, player_id, message: LCDMessage) -> None:
        """
        Display a message on a specific player's LCD screen.

        Args:
            player_id: ID of the target player
            message: LCDMessage object containing display content
        """
        topic = PLAYERS_LCD_TOPIC.format(id=player_id)
        payload = message.toJson()
        self.client.publish(topic, payload)
        self.printDebug(f"(Player {player_id} LCD) {message}")

    def showInOtherLCD(self, player_id, message: LCDMessage) -> None:
        """
        Display a message on all LCD screens except the specified player's.

        Args:
            player_id: ID of the player to exclude
            message: LCDMessage object containing display content
        """
        for other in self.players:
            if other.id != player_id:
                self.showInLCD(other.id, message)

    def showInAllLCD(self, message: LCDMessage) -> None:
        """
        Display a message on all players' LCD screens.

        Args:
            message: LCDMessage object containing display content
        """
        for player in self.players:
            self.showInLCD(player.id, message)

    def playInBuzzer(self, player_id, message: BuzzerMessage) -> None:
        """
        Play a sound on a specific player's buzzer.

        Args:
            player_id: ID of the target player
            message: BuzzerMessage object containing sound parameters
        """
        topic = PLAYERS_BUZZER_TOPIC.format(id=player_id)
        payload = message.toJson()
        self.client.publish(topic, payload)
        self.printDebug(f"(Player {player_id} Buzzer) {message}")

    def playInOtherBuzzer(self, player_id, message: BuzzerMessage) -> None:
        """
        Play a sound on all buzzers except the specified player's.

        Args:
            player_id: ID of the player to exclude
            message: BuzzerMessage object containing sound parameters
        """
        for other in self.players:
            if other.id != player_id:
                self.playInBuzzer(other.id, message)

    def playInAllBuzzer(self, message: BuzzerMessage) -> None:
        """
        Play a sound on all players' buzzers.

        Args:
            message: BuzzerMessage object containing sound parameters
        """
        for player in self.players:
            self.playInBuzzer(player.id, message)

    def beepPlayer(self, player_id, duration_ms=100, frequency=1000):
        """
        Make a single player's buzzer beep with specified parameters.

        Args:
            player_id: ID of the target player
            duration_ms: Duration of the beep in milliseconds (default: 100)
            frequency: Frequency of the beep in Hz (default: 1000)
        """
        message = BuzzerMessage(tones=[frequency, 0], duration=[duration_ms, 0])
        self.playInBuzzer(player_id, message)
        self.printDebug(f"Player {player_id} is beeping at {frequency}Hz for {duration_ms}ms")

    def beepOtherPlayers(self, player_id, duration_ms=100, frequency=1000):
        """
        Make all other players' buzzers beep except the specified player.

        Args:
            player_id: ID of the player to exclude
            duration_ms: Duration of the beep in milliseconds (default: 100)
            frequency: Frequency of the beep in Hz (default: 1000)
        """
        message = BuzzerMessage(tones=[frequency, 0], duration=[duration_ms, 0])
        for other in self.players:
            if other.id != player_id:
                self.playInBuzzer(other.id, message)

    def beepAllPlayers(self, duration_ms=100, frequency=1000):
        """
        Make all players' buzzers beep simultaneously.

        Args:
            duration_ms: Duration of the beep in milliseconds (default: 100)
            frequency: Frequency of the beep in Hz (default: 1000)
        """
        message = BuzzerMessage(tones=[frequency, 0], duration=[duration_ms, 0])
        for player in self.players:
            self.playInBuzzer(player.id, message)
