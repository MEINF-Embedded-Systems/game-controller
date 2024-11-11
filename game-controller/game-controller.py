import time
import paho.mqtt.client as mqtt
from GameState import GameState
from threading import Event
from colorama import Fore

# Debug mode
DEBUG = True

# Game parameters
NUM_PLAYERS = 2
players = [False] * NUM_PLAYERS

# MQTT parameters
CLIENT_ID = "game-controller"
MQTT_BROKER = "mosquitto"
MQTT_PORT = 1883

# Topics
PLAYERS_CONNECTION_TOPIC = "game/players/+/connection"

# Events
waitPlayersEvent = Event()

# Current state of the game
current_state = GameState.WAITING_FOR_PLAYERS


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
    client.subscribe(PLAYERS_CONNECTION_TOPIC)
    print("Waiting for players to connect...")
    waitPlayersEvent.wait()
    print("All players connected!")
    setGameState(GameState.PLAYING)


def managePlayersConnection(message: mqtt.MQTTMessage) -> None:
    player_id = int(message.topic.split("/")[2])
    if 1 <= player_id <= len(players):
        players[player_id - 1] = True
        print(f"Player {player_id} connected")
        if all(players):
            waitPlayersEvent.set()
    else:
        print(f"Player {player_id} is not allowed to connect")


def closeMqttConnection(client: mqtt.Client) -> None:
    client.loop_stop()
    client.disconnect()


# Callbacks
def on_message(client, userdata, message):
    printDebug(f"Message recevived: {message.payload.decode()}")
    match current_state:
        case GameState.WAITING_FOR_PLAYERS:
            managePlayersConnection(message)
        case _:
            print("No state defined")


if __name__ == "__main__":
    try:
        client = createMqttClient(MQTT_BROKER, MQTT_PORT, CLIENT_ID)
        waitForPlayers()
    except KeyboardInterrupt:
        print("Program terminated by user")
    except Exception as e:
        print("An unexpected error occurred:", e)
    finally:
        print("Exiting...")
        closeMqttConnection(client)
