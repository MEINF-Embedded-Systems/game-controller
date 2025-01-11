import json
import time
import paho.mqtt.client as mqtt

import Melodies

from random import Random
from CellType import CellType
from GameState import GameState
from threading import Event
from Player import Player
from Utils import Utils, LCDMessage
from boards import *
from minigames import *

# Debug mode
DEBUG = False

# Game parameters
NUM_PLAYERS = 2
players = [Player(i) for i in range(1, NUM_PLAYERS + 1)]
WIN_POINTS = 100

# MQTT parameters
CLIENT_ID = "game-controller"
MQTT_BROKER = "mosquitto"
MQTT_PORT = 1883

# Topics
# Components
PLAYERS_CONNECTION_TOPIC = "game/players/{id}/connection"
PLAYERS_LCD_TOPIC = "game/players/{id}/components/lcd"
PLAYERS_BUZZER_TOPIC = "game/players/{id}/components/buzzer"
# PLAYERS_LED_TOPIC = "game/players/{id}/components/led"
PLAYERS_BUTTON_TOPIC = "game/players/{id}/components/button"
PLAYERS_TURN_TOPIC = "game/players/{id}/turn"
PLAYERS_HALL_SENSOR_TOPIC = "game/players/{id}/movement"

# Events
waitPlayersEvent = Event()
waitDiceEvent = Event()
waitMovementEvent = Event()
waitMinigameElectionEvent = Event()

# Current state of the game
current_state = GameState.WAITING_FOR_PLAYERS
turn = 0
board = DebugBoard() if DEBUG else DebugBoard()


minigames = {
    MinigameType.Hot_Potato: HotPotato,
    MinigameType.Number_Guesser: NumberGuesser,
    MinigameType.Tug_of_War: TugOfWar,
    MinigameType.Last_Stick_Standing: LastStickStanding,
    # MinigameType.Blind_Timer: Minigame,
    # MinigameType.Rock_Paper_Scissors: Minigame,
    # MinigameType.Quick_Reflexes: Minigame,
}

current_minigame: Minigame = None

# Only for debug mode
orderedMinigames: list[MinigameType] = list(sorted(minigames, key=lambda x: x.name))
randomGameDebug: MinigameType = None
minigameIndex: int = 0


# Callbacks
def on_message(client, userdata, message):
    match current_state:
        case GameState.WAITING_FOR_PLAYERS:
            managePlayersConnection(message)
        case GameState.ROLLING_DICE:
            manageDiceRoll(message)
        case GameState.MINIGAME:
            current_minigame.handleMQTTMessage(message)
        case GameState.MOVING:
            managePlayerHallSensor(message)
        case GameState.MINIGAME_ELECTION:  # Only for debug mode
            manageGameElectionManually(message)
        case _:
            pass


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
            utils.showInLCD(
                player_id,
                LCDMessage(top="Connected".center(16), down=f"You are Player {player_id}"),
            )
            if all(player.connected for player in players):
                waitPlayersEvent.set()
    else:
        print(f"Player {player_id} is not allowed to connect")


def manageDiceRoll(message: mqtt.MQTTMessage) -> None:
    if message.topic == PLAYERS_BUTTON_TOPIC.format(id=players[turn].id):
        waitDiceEvent.set()


def manageGameElectionManually(message: mqtt.MQTTMessage) -> None:
    global randomGameDebug
    global minigameIndex
    global orderedMinigames
    if message.topic == PLAYERS_BUTTON_TOPIC.format(id=players[turn].id):
        payload = json.loads(message.payload.decode())
        if payload["type"] == "short":
            minigameIndex = (minigameIndex + 1) % len(orderedMinigames)
            nextMinigame: MinigameType = orderedMinigames[minigameIndex]
            utils.showInAllLCD(LCDMessage(top=nextMinigame.name.center(16)))
        elif payload["type"] == "long":
            randomGameDebug = orderedMinigames[minigameIndex]
            minigameIndex = 0
            waitMinigameElectionEvent.set()


def managePlayerHallSensor(message: mqtt.MQTTMessage) -> None:
    if message.topic == PLAYERS_HALL_SENSOR_TOPIC.format(id=players[turn].id):
        waitMovementEvent.set()


def closeMqttConnection(client: mqtt.Client) -> None:
    client.loop_stop()
    client.disconnect()


def initGame() -> None:
    global turn
    winner = None
    setGameState(GameState.PLAYING)
    utils.showInAllLCD(LCDMessage(top="Welcome to".center(16), down="The Game".center(16)))
    utils.playInAllBuzzer(Melodies.GAME_TUNE)
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

    # Check if player is skipped
    if player.skipped:
        utils.showInLCD(player.id, LCDMessage(top="Turn skipped!".center(16)))
        utils.showInOtherLCD(
            player.id, LCDMessage(top=f"Player {player.id}'s".center(16), down="turn skipped!".center(16))
        )
        player.skipped = False
        time.sleep(3)
        return

    # Publish the player's turn
    client.publish(PLAYERS_TURN_TOPIC.format(id=player.id), 1)

    # Play your turn sound
    utils.playInBuzzer(player.id, Melodies.YOUR_TURN_SOUND)
    # Show the player's turn in the LCDs
    utils.showInLCD(player.id, LCDMessage(top="Your turn!".center(16)))
    utils.showInOtherLCD(player.id, LCDMessage(top=f"Player {player.id} turn!".center(16)))
    time.sleep(3)

    # Roll the dice and play the turn
    dice = rollDice(player)
    movePlayer(player, dice)
    playCell(player, board.getCellType(player.position))
    client.publish(PLAYERS_TURN_TOPIC.format(id=player.id), 0)


def movePlayer(player: Player, steps: int) -> None:
    moveWithHallSensor(player, steps)
    utils.showInLCD(player.id, LCDMessage(top="Moved to cell".center(16), down=f"{player.position}".center(16)))
    utils.showInOtherLCD(
        player.id, LCDMessage(top=f"Player {player.id} moved".center(16), down=f"to cell {player.position}".center(16))
    )
    print(f"Player {player.id} moved to cell {player.position} - {board.getCellName(player.position)}")
    time.sleep(4)


def moveWithHallSensor(player: Player, dice: int) -> None:
    setGameState(GameState.MOVING)
    client.subscribe(PLAYERS_HALL_SENSOR_TOPIC.format(id=player.id))

    for i in range(dice, 0, -1):
        utils.showInLCD(player.id, LCDMessage(top="Move the meeple".center(16), down=f"{i} moves left".center(16)))
        utils.showInOtherLCD(
            player.id, LCDMessage(top=f"P{player.id} moving".center(16), down=f"{i}moves left".center(16))
        )
        waitEvent(waitMovementEvent)
        # Play the sound of the movement
        utils.playInAllBuzzer(Melodies.MOVE_SOUND)

    client.unsubscribe(PLAYERS_HALL_SENSOR_TOPIC.format(id=player.id))
    player.moveForward(dice, board.size)


def rollDice(player) -> int:
    setGameState(GameState.ROLLING_DICE)

    topic = PLAYERS_BUTTON_TOPIC.format(id=player.id)

    message = LCDMessage(top="Roll the dice".center(16), down="Press the button".center(16))
    utils.showInLCD(player.id, message)

    client.subscribe(topic)
    waitEvent(waitDiceEvent)
    client.unsubscribe(topic)
    result = 1

    message = LCDMessage(top="Dice rolled".center(16), down=str(result).center(16))
    utils.showInLCD(player.id, message)
    utils.showInOtherLCD(
        player.id, LCDMessage(top=f"Player {player.id} rolled".center(16), down=str(result).center(16))
    )
    time.sleep(4)
    return result


def waitEvent(event: Event) -> bool:
    res = event.wait()
    event.clear()
    return res


def playCell(player: Player, cell_type: CellType) -> None:
    setGameState(GameState.PLAYING)
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
    utils.playInAllBuzzer(Melodies.GAIN_POINTS_TUNE)
    messagePlayer = LCDMessage(top="Gain Points".center(16))
    utils.showInLCD(player.id, messagePlayer)
    utils.showInOtherLCD(
        player.id, LCDMessage(top="Player {player.id} landed".center(16), down="on Gain Points".center(16))
    )
    time.sleep(4)
    points = Random().randint(5, 10)
    player.gainPoints(points)
    messagePlayer = LCDMessage(top="You gained".center(16), down=f"{points:2d} points".center(16))
    messageOther = LCDMessage(
        top=f"Player {player.id} gained".center(16),
        down=f"{points:2d} points".center(16),
    )
    utils.showInLCD(player.id, messagePlayer)
    utils.showInOtherLCD(player.id, messageOther)
    time.sleep(4)


def losePoints(player: Player) -> None:
    utils.playInAllBuzzer(Melodies.LOSE_POINTS_TUNE)
    messagePlayer = LCDMessage(top="Lose Points".center(16))
    utils.showInLCD(player.id, messagePlayer)
    utils.showInOtherLCD(
        player.id, LCDMessage(top="Player {player.id} landed".center(16), down="on Lose Points".center(16))
    )
    time.sleep(4)
    points = Random().randint(1, 5)
    player.losePoints(points)
    messagePlayer = LCDMessage(top="You lost".center(16), down=f"{points:2d} points".center(16))
    messageOther = LCDMessage(top=f"Player {player.id} lost".center(16), down=f"{points:2d} points".center(16))
    utils.showInLCD(player.id, messagePlayer)
    utils.showInOtherLCD(player.id, messageOther)
    time.sleep(4)


def skipTurn(player: Player) -> None:
    utils.playInAllBuzzer(Melodies.SKIP_TURN_TUNE)
    utils.showInLCD(player.id, LCDMessage(top="Skip Turn".center(16)))
    utils.showInOtherLCD(
        player.id, LCDMessage(top=f"Player {player.id} landed".center(16), down="on Skip Turn".center(16))
    )
    time.sleep(4)

    utils.showInLCD(player.id, LCDMessage(top="You will lose".center(16), down="next turn".center(16)))
    time.sleep(2)

    # Set skipped status for next turn
    player.skipped = True


def randomEvent(player: Player) -> None:
    utils.playInAllBuzzer(Melodies.RANDOM_EVENT_TUNE)
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
    utils.showInOtherLCD(
        player.id, LCDMessage(top="Player {player.id} landed".center(16), down="on Random Event".center(16))
    )
    time.sleep(4)

    # Selection animation
    animateOptions(utils, [str(event.value) for event in events])

    # Play the selected event
    playCell(player, random_event)
    time.sleep(4)


def moveForward(player: Player) -> None:
    utils.playInAllBuzzer(Melodies.MOVE_FORWARD_TUNE)
    utils.showInLCD(player.id, LCDMessage(top="Move Forward".center(16)))
    utils.showInOtherLCD(
        player.id, LCDMessage(top="Player {player.id} landed".center(16), down="on Move Forward".center(16))
    )
    time.sleep(4)
    steps = Random().randint(1, 3)
    utils.showInLCD(player.id, LCDMessage(top=f"Move {steps}".center(16), down="steps forward".center(16)))
    utils.showInOtherLCD(
        player.id, LCDMessage(top=f"Player {player.id} moves".center(16), down=f"{steps} steps forward".center(16))
    )
    time.sleep(4)
    movePlayer(player, steps)
    playCell(player, board.getCellType(player.position))
    time.sleep(4)


def moveBackward(player: Player) -> None:
    utils.playInAllBuzzer(Melodies.MOVE_BACKWARD_TUNE)
    utils.showInLCD(player.id, LCDMessage(top="Move Backwards".center(16)))
    utils.showInOtherLCD(
        player.id, LCDMessage(top="Player {player.id} landed".center(16), down="on Move Backward".center(16))
    )
    time.sleep(4)
    steps = Random().randint(1, 3)
    utils.showInLCD(player.id, LCDMessage(top=f"Move {steps}".center(16), down="steps backward".center(16)))
    utils.showInOtherLCD(
        player.id, LCDMessage(top=f"Player {player.id}".center(16), down=f"moves {steps} steps back".center(16))
    )
    time.sleep(4)
    movePlayer(player, -steps)
    playCell(player, board.getCellType(player.position))
    time.sleep(4)


def deathEvent(player: Player) -> None:
    utils.playInAllBuzzer(Melodies.DEATH_TUNE)
    message = LCDMessage(top="Death Event".center(16))
    utils.showInLCD(player.id, message)
    utils.showInOtherLCD(
        player.id, LCDMessage(top="Player {player.id} landed".center(16), down="on Death Event".center(16))
    )
    time.sleep(4)
    message = LCDMessage(top="You died".center(16))
    utils.showInLCD(player.id, message)
    utils.showInOtherLCD(player.id, LCDMessage(top="Player {player.id} died".center(16)))
    time.sleep(2)
    message = LCDMessage(top="You lose".center(16), down="all your points".center(16))
    utils.showInLCD(player.id, message)
    utils.showInOtherLCD(player.id, LCDMessage(top="Player {player.id} lost".center(16), down="all points".center(16)))
    player.losePoints(player.points)
    time.sleep(4)


def showStats() -> None:
    message = LCDMessage(
        top=f"P{players[0].id}: {players[0].points} points",
        down=f"P{players[1].id}: {players[1].points} points",
    )
    utils.showInAllLCD(message)
    time.sleep(5)


def animateOptions(utils: Utils, options: list[str]) -> None:
    """Animates a selection from a list of options on the LCD screens.

    Args:
        utils: The Utils instance for interacting with the LCDs.
        options: A list of strings representing the options.
    """
    animation_duration = 3  # Total animation time in seconds
    frames_per_second = 5  # Number of options displayed per second
    num_frames = int(animation_duration * frames_per_second)

    # Sound effect
    utils.playInAllBuzzer(Melodies.SELECTION_SOUND)

    for i in range(num_frames):
        current_index = i % len(options)  # Cycle through all options
        utils.showInAllLCD(LCDMessage(top=options[current_index].center(16)))
        time.sleep(1 / frames_per_second)

    utils.showInAllLCD(LCDMessage(top=" "))  # Clear the LCD at the end of the animation


def miniGame() -> None:
    global current_minigame

    utils.playInAllBuzzer(Melodies.MINIGAME_CELL_TUNE)
    utils.showInAllLCD(LCDMessage(top="Minigame Time!".center(16)))
    time.sleep(4)

    winning_points = 10
    randomGame = getRandomGame()
    current_minigame = minigames[randomGame](players, client, DEBUG)
    setGameState(GameState.MINIGAME)
    print(f"Playing minigame: {randomGame.name}")
    winners: list[Player] = current_minigame.playGame()
    handleWinners(winners, winning_points)
    time.sleep(4)


def getRandomGame() -> MinigameType:
    game = None
    if DEBUG:
        game = waitForMinigameElection()
    else:
        # Animate the minigame selection
        minigame_names = [str(game.name) for game in minigames.keys()]
        animateOptions(utils, minigame_names)
        game = Random().choice(list(minigames.keys()))
    return game


def waitForMinigameElection() -> MinigameType:
    global randomGameDebug
    global orderedMinigames
    client.subscribe(PLAYERS_BUTTON_TOPIC.format(id=players[turn].id))
    utils.showInAllLCD(LCDMessage(top=orderedMinigames[0].name.center(16)))
    setGameState(GameState.MINIGAME_ELECTION)
    waitEvent(waitMinigameElectionEvent)
    client.unsubscribe(PLAYERS_BUTTON_TOPIC.format(id=players[turn].id))
    return randomGameDebug


def handleWinners(winners: list[Player], winning_points: int) -> None:
    # NO WINNERS
    if len(winners) == 0:
        utils.showInAllLCD(LCDMessage(top="No winners".center(16), down="0 points".center(16)))
        utils.playInAllBuzzer(Melodies.LOSING_SOUND)

    # 1 WINNER
    elif len(winners) == 1:
        # Update points
        winner = winners[0]
        winner.gainPoints(winning_points)

        # Feedback
        # Buzzers -> winning/losing sound
        utils.playInBuzzer(winner.id, Melodies.WINNING_SOUND)
        utils.playInOtherBuzzer(winner.id, Melodies.LOSING_SOUND)

        # You won/lost message
        utils.showInLCD(winner.id, LCDMessage(top="You won!".center(16)))
        utils.showInOtherLCD(winner.id, LCDMessage(top="You lost".center(16)))
        time.sleep(3)

        # Congratulations message
        utils.showInLCD(winner.id, LCDMessage(top="Great job!".center(16), down="Congratulations!".center(16)))
        utils.showInOtherLCD(
            winner.id,
            LCDMessage(top="Better luck".center(16), down="next time".center(16)),
        )
        time.sleep(3)

        # Points feedback
        utils.showInLCD(winner.id, LCDMessage(top="You won".center(16), down=f"{winning_points} points".center(16)))
        utils.showInOtherLCD(
            winner.id, LCDMessage(top=f"Player {winner.id} won".center(16), down=f"{winning_points} points".center(16))
        )
        time.sleep(3)

    # MULTIPLE WINNERS -> DRAW
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
