from random import Random
import time
from CellType import CellType
import paho.mqtt.client as mqtt
from GameState import GameState
from threading import Event
from colorama import Fore
from Player import Player
from Board import Board
from Message import Message

# Debug mode
DEBUG = True

# Game parameters
NUM_PLAYERS = 2
players = [Player(i) for i in range(1, NUM_PLAYERS + 1)]
WIN_POINTS = 100

# MQTT parameters
CLIENT_ID = "game-controller"
MQTT_BROKER = "mosquitto"
MQTT_PORT = 1883

# Topics
PLAYERS_CONNECTION_TOPIC = "game/players/{id}/connection"
PLAYERS_LCD_TOPIC = "game/players/{id}/components/lcd"
PLAYERS_BUZZER_TOPIC = "game/players/{id}/components/buzzer"
PLAYERS_LED_TOPIC = "game/players/{id}/components/led"
PLAYERS_BUTTON_TOPIC = "game/players/{id}/components/button"

# Events
waitPlayersEvent = Event()
waitDiceEvent = Event()

# Current state of the game
current_state = GameState.WAITING_FOR_PLAYERS
turn = 0
board = Board()


# Callbacks
def on_message(client, userdata, message):
    printDebug(f"Message recevived: {message.payload.decode()}")
    match current_state:
        case GameState.WAITING_FOR_PLAYERS:
            managePlayersConnection(message)
        case GameState.ROLLING_DICE:
            manageDiceRoll(message)
        case _:
            print("No state defined")


# Functions
def printDebug(message: str) -> None:
    if DEBUG:
        print(Fore.YELLOW + f"DEBUG: {message}" + Fore.RESET)


def setGameState(state: GameState) -> None:
    global current_state
    printDebug(f"Game state changed to {state.name}")
    current_state = state


def createMqttClient(broker: str, port: int, client_id: str) -> mqtt.Client:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    client.on_message = on_message
    print("Connecting to broker...")
    while client.connect(broker, port) != mqtt.MQTT_ERR_SUCCESS:
        print("Connection failed, retrying...")
        time.sleep(1)
    print("Connected!")
    client.loop_start()
    return client


def waitForPlayers() -> None:
    setGameState(GameState.WAITING_FOR_PLAYERS)
    client.subscribe(PLAYERS_CONNECTION_TOPIC.format(id="+"))
    print("Waiting for players to connect...")
    waitEvent(waitPlayersEvent)
    print("All players connected!")


def managePlayersConnection(message: mqtt.MQTTMessage) -> None:
    player_id = int(message.topic.split("/")[2])
    if 1 <= player_id <= len(players):
        players[player_id - 1].connected = True
        print(f"Player {player_id} connected")
        if all(player.connected for player in players):
            waitPlayersEvent.set()
    else:
        print(f"Player {player_id} is not allowed to connect")


def manageDiceRoll(message: mqtt.MQTTMessage) -> None:
    player_id = int(message.topic.split("/")[2])
    if player_id == players[turn].player_id:
        waitDiceEvent.set()
    else:
        print(f"Player {player_id} is not allowed to roll the dice")


def closeMqttConnection(client: mqtt.Client) -> None:
    client.loop_stop()
    client.disconnect()


def initGame() -> None:
    global turn

    setGameState(GameState.PLAYING)
    while current_state != GameState.GAME_OVER:
        playTurn(players[turn])
        turn = (turn + 1) % NUM_PLAYERS
        time.sleep(2)


def playTurn(player: Player) -> None:
    print(f"Player {player.player_id} turn!")
    message = Message(top="Your turn".center(16), time=2000)
    showInLCD(player.player_id, message)
    movePlayer(player)
    playCell(player, board.getCellType(player.position))


def movePlayer(player: Player) -> None:
    player.moveForward(rollDice(player), board.size)
    message = Message(top=f"Moved to cell {player.position}", time=2000)
    showInLCD(player.player_id, message)
    print(
        f"Player {player.player_id} moved to cell {player.position} - {board.getCellName(player.position)}"
    )


def rollDice(player) -> int:
    setGameState(GameState.ROLLING_DICE)

    topic = PLAYERS_BUTTON_TOPIC.format(id=player.player_id)
    client.subscribe(topic)
    message = Message(
        top="Roll your dice".center(16), down="Press the button".center(16), time=2000
    )
    showInLCD(player.player_id, message)
    waitEvent(waitDiceEvent)
    result = Random().randint(1, 1)
    message = Message(
        top="Dice rolled".center(16), down=str(result).center(16), time=2000
    )
    showInLCD(player.player_id, message)
    client.unsubscribe(topic)

    setGameState(GameState.PLAYING)
    return result


def waitEvent(event: Event) -> bool:
    res = event.wait()
    event.clear()
    return res


def playCell(player: Player, cell_type: CellType) -> None:
    match cell_type:
        case CellType.GP:
            gainPoints(player)
        case CellType.LP:
            pass
        case CellType.MF:
            pass
        case CellType.MG:
            pass
        case CellType.MB:
            pass
        case CellType.DE:
            pass
        case CellType.SK:
            pass
        case CellType.RE:
            pass


def gainPoints(player: Player) -> None:
    player.gainPoints(10)
    message = Message(
        top="You gained".center(16), down="10 points".center(16), time=2000
    )
    showInLCD(player.player_id, message)


def showInLCD(player_id, message: Message) -> None:
    topic = PLAYERS_LCD_TOPIC.format(id=player_id)
    payload = message.toJson()
    client.publish(topic, payload)
    printDebug(f"(Player {player_id}) {message}")


if __name__ == "__main__":
    try:
        client = createMqttClient(MQTT_BROKER, MQTT_PORT, CLIENT_ID)
        waitForPlayers()
        initGame()
        for player in players:
            print(player)
    except KeyboardInterrupt:
        print("Program terminated by user")
    except Exception as e:
        print("An unexpected error occurred:", e)
    finally:
        print("Exiting...")
        closeMqttConnection(client)
