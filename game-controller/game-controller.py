from random import Random
import time
from CellType import CellType
import paho.mqtt.client as mqtt
from GameState import GameState
from threading import Event
from Player import Player
from Board import Board
from Message import LCDMessage
from minigames import *
from Utils import Utils
import Melodies

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
PLAYERS_TURN_TOPIC = "game/players/{id}/turn"

MINIGAMES_TOPIC = "game/minigame"

# Events
waitPlayersEvent = Event()
waitDiceEvent = Event()

# Current state of the game
current_state = GameState.WAITING_FOR_PLAYERS
turn = 0
board = Board()

minigames = {
    MinigameType.Hot_Potato: Minigame,
    MinigameType.Blind_Timer: Minigame,
    MinigameType.Number_Guesser: NumberGuesser,
    MinigameType.Tug_of_War: Minigame,
    MinigameType.Rock_Paper_Scissors: Minigame,
    MinigameType.Last_Stick_Standing: Minigame,
    MinigameType.Quick_Reflexes: Minigame,
}

current_minigame: Minigame = None


# Callbacks
def on_message(client, userdata, message):
    # utils.printDebug(f"LCDMessage recevived: {message.payload.decode()}")
    match current_state:
        case GameState.WAITING_FOR_PLAYERS:
            managePlayersConnection(message)
        case GameState.ROLLING_DICE:
            manageDiceRoll(message)
        case GameState.MINIGAME:
            current_minigame.handleMQTTMessage(message)
        case GameState.GAME_OVER:
            pass
        case _:
            pass
            # print("No state defined")


def setGameState(state: GameState) -> None:
    global current_state
    utils.printDebug(f"Game state changed to {state.name}")
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
    time.sleep(2)


def managePlayersConnection(message: mqtt.MQTTMessage) -> None:
    player_id = int(message.topic.split("/")[2])
    if 1 <= player_id <= len(players):
        if not players[player_id - 1].connected:
            players[player_id - 1].connected = True
            print(f"Player {player_id} connected")
            utils.showInLCD(player_id, LCDMessage(top="Connected".center(16), down=f"You are Player {player_id}"))
            if all(player.connected for player in players):
                waitPlayersEvent.set()
    else:
        print(f"Player {player_id} is not allowed to connect")


def manageDiceRoll(message: mqtt.MQTTMessage) -> None:
    if message.topic == PLAYERS_BUTTON_TOPIC.format(id=players[turn].id):
        player_id = int(message.topic.split("/")[2])
        if player_id == players[turn].id:
            waitDiceEvent.set()
        else:
            print(f"Player {player_id} is not allowed to roll the dice")


def closeMqttConnection(client: mqtt.Client) -> None:
    client.loop_stop()
    client.disconnect()


def initGame() -> None:
    global turn
    winner = None
    setGameState(GameState.PLAYING)
    utils.showInAllLCD(LCDMessage(top="Welcome to".center(16), down="The Game".center(16)))
    utils.playInAllBuzzer(Melodies.WINNING_SOUND)
    utils.playInAllBuzzer(Melodies.LOSING_SOUND)
    time.sleep(5)

    while current_state != GameState.GAME_OVER:
        playTurn(players[turn])
        showStats()
        turn = (turn + 1) % NUM_PLAYERS
        time.sleep(2)
        if players[turn].points >= WIN_POINTS:
            winner = players[turn]
            setGameState(GameState.GAME_OVER)

    message = LCDMessage(top="Game Over".center(16), down=f"Player {winner.id} wins!".center(16))
    utils.showInAllLCD(message)
    time.sleep(5)


def playTurn(player: Player) -> None:
    print(f"Player {player.id} turn!")
    client.publish(PLAYERS_TURN_TOPIC.format(id=player.id), "1")

    utils.showInLCD(player.id, LCDMessage(top="Your turn".center(16)))
    utils.showInOtherLCD(player.id, LCDMessage(top=f"Player {player.id} turn!".center(16)))

    time.sleep(3)

    movePlayer(player)
    # playCell(player, board.getCellType(player.position))
    playCell(player, CellType.MG)
    client.publish(PLAYERS_TURN_TOPIC.format(id=player.id), "0")


def movePlayer(player: Player) -> None:
    player.moveForward(rollDice(player), board.size)
    # TODO: Interact with hall sensor
    utils.showInLCD(player.id, LCDMessage(top=f"Moved to cell {player.position}"))
    print(f"Player {player.id} moved to cell {player.position} - {board.getCellName(player.position)}")
    time.sleep(4)


def rollDice(player) -> int:
    setGameState(GameState.ROLLING_DICE)

    topic = PLAYERS_BUTTON_TOPIC.format(id=player.id)
    client.subscribe(topic)
    message = LCDMessage(top="Roll the dice".center(16), down="Press the button".center(16))
    utils.showInLCD(player.id, message)
    waitEvent(waitDiceEvent)
    result = Random().randint(1, 6)
    message = LCDMessage(top="Dice rolled".center(16), down=str(result).center(16))
    utils.showInLCD(player.id, message)
    client.unsubscribe(topic)

    setGameState(GameState.PLAYING)
    time.sleep(4)
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
            losePoints(player)
        case CellType.MF:
            moveForward(player)
        case CellType.MG:
            miniGame()
        case CellType.MB:
            moveBackward(player)
        case CellType.DE:
            deathEvent(player)
        case CellType.SK:
            skipTurn(player)
        case CellType.RE:
            randomEvent(player)


def gainPoints(player: Player) -> None:
    messagePlayer = LCDMessage(top="Gain Points".center(16))
    utils.showInLCD(player.id, messagePlayer)
    time.sleep(4)
    points = Random().randint(5, 10)
    player.gainPoints(points)
    messagePlayer = LCDMessage(top="You gained".center(16), down=f"{points:2d} points".center(16))
    messageOther = LCDMessage(top=f"Player {player.id} gained".center(16), down=f"{points:2d} points".center(16))
    utils.showInLCD(player.id, messagePlayer)
    utils.showInOtherLCD(player.id, messageOther)
    time.sleep(4)


def losePoints(player: Player) -> None:
    messagePlayer = LCDMessage(top="Lose Points".center(16))
    utils.showInLCD(player.id, messagePlayer)
    time.sleep(4)
    points = Random().randint(1, 5)
    player.losePoints(points)
    messagePlayer = LCDMessage(top="You lost".center(16), down=f"{points:2d} points".center(16))
    messageOther = LCDMessage(top=f"Player {player.id} lost".center(16), down=f"{points:2d} points".center(16))
    utils.showInLCD(player.id, messagePlayer)
    utils.showInOtherLCD(player.id, messageOther)
    time.sleep(4)


def skipTurn(player: Player) -> None:
    message = LCDMessage(top="Skip turn".center(16))
    utils.showInLCD(player.id, message)
    time.sleep(4)


def randomEvent(player: Player) -> None:
    eventProbs = {
        CellType.MF: 1 / 5,
        CellType.MB: 1 / 5,
        CellType.GP: 1 / 5,
        CellType.LP: 1 / 5,
        CellType.SK: 1 / 5,
    }
    events, probs = zip(*eventProbs.items())
    random_event = Random().choices(events, probs)[0]
    message = LCDMessage(top="Random Event".center(16))
    utils.showInLCD(player.id, message)
    time.sleep(4)
    playCell(player, random_event)
    time.sleep(4)


def moveForward(player: Player) -> None:
    message = LCDMessage(top="Move Forward".center(16))
    utils.showInLCD(player.id, message)
    time.sleep(4)
    steps = Random().randint(1, 3)
    player.moveForward(steps, board.size)
    message = LCDMessage(top=f"Move {steps}".center(16), down="steps forward".center(16))
    utils.showInLCD(player.id, message)
    time.sleep(4)
    playCell(player, board.getCellType(player.position))
    time.sleep(4)


def moveBackward(player: Player) -> None:
    message = LCDMessage(top="Move Backwards".center(16))
    utils.showInLCD(player.id, message)
    time.sleep(4)
    steps = Random().randint(1, 3)
    player.moveBackward(steps, board.size)
    message = LCDMessage(top=f"Move {steps}".center(16), down="steps backward".center(16))
    utils.showInLCD(player.id, message)
    time.sleep(4)
    playCell(player, board.getCellType(player.position))
    time.sleep(4)


def deathEvent(player: Player) -> None:
    message = LCDMessage(top="Death Event".center(16))
    utils.showInLCD(player.id, message)
    time.sleep(4)
    message = LCDMessage(top="You died".center(16))
    utils.showInLCD(player.id, message)
    time.sleep(2)
    message = LCDMessage(top="You lose".center(16), down="all your points".center(16))
    utils.showInLCD(player.id, message)
    player.losePoints(player.points)
    time.sleep(4)


def showStats() -> None:
    message = LCDMessage(
        top=f"P{players[0].id}: {players[0].points} points",
        down=f"P{players[1].id}: {players[1].points} points",
    )
    utils.showInAllLCD(message)
    time.sleep(5)


def miniGame() -> None:
    global current_minigame
    winning_points = 10
    # randomGame: MinigameType = Random().choice(list(minigames.keys()))
    randomGame = MinigameType.Number_Guesser
    current_minigame = minigames[randomGame](players, client)

    setGameState(GameState.MINIGAME)
    print(f"Playing minigame: {randomGame.name}")
    # client.publish(MINIGAMES_TOPIC, randomGame.value)
    winners: list[Player] = current_minigame.playGame()
    handleWinners(winners, winning_points)
    time.sleep(4)


def handleWinners(winners: list[Player], winning_points: int) -> None:
    if len(winners) == 0:
        utils.showInAllLCD(LCDMessage(top="No winners".center(16), down="0 points".center(16)))
        utils.playInAllBuzzer(Melodies.LOSING_SOUND)
    elif len(winners) == 1:
        winner = winners[0]
        winner.gainPoints(winning_points)
        utils.showInLCD(winner.id, LCDMessage(top="You won".center(16), down=f"{winning_points} points".center(16)))
        utils.playInBuzzer(winner.id, Melodies.WINNING_SOUND)
        utils.playInOtherBuzzer(winner.id, Melodies.LOSING_SOUND)
        utils.showInOtherLCD(
            winner.id, LCDMessage(top=f"Player {winner.id} won".center(16), down=f"{winning_points} points".center(16))
        )
        time.sleep(2)
        utils.showInOtherLCD(winner.id, LCDMessage(top="Better luck".center(16), down="next time".center(16)))
    else:
        utils.showInAllLCD(LCDMessage(top="Draw!", down=f"{winning_points} points"))
        for winner in winners:
            winner.gainPoints(winning_points // len(winners))
            utils.playInBuzzer(winner.id, Melodies.WINNING_SOUND)


if __name__ == "__main__":
    try:
        client = createMqttClient(MQTT_BROKER, MQTT_PORT, CLIENT_ID)
        utils = Utils(client, players, DEBUG)
        waitForPlayers()
        initGame()
    except KeyboardInterrupt:
        print("Program terminated by user")
    except Exception as e:
        print("An unexpected error occurred:", e)
    finally:
        print("Exiting...")
        closeMqttConnection(client)
