#######################
# IMPORTS AND MODULES #
#######################
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

"""
Main game controller module that manages the game flow, player interactions, and game states.
Handles MQTT communication between players and coordinates all game events and minigames.
"""

########################
# CONFIGURATION & STATE #
########################

# Debug configuration
DEBUG = False

# Game configuration
NUM_PLAYERS = 2
players = [Player(i) for i in range(1, NUM_PLAYERS + 1)]
WIN_POINTS = 50

# MQTT configuration
CLIENT_ID = "game-controller"
MQTT_BROKER = "mosquitto"
MQTT_PORT = 1883

######################
# MQTT TOPIC STRINGS #
######################
# Components
PLAYERS_CONNECTION_TOPIC = "game/players/{id}/connection"
PLAYERS_LCD_TOPIC = "game/players/{id}/components/lcd"
PLAYERS_BUZZER_TOPIC = "game/players/{id}/components/buzzer"
PLAYERS_BUTTON_TOPIC = "game/players/{id}/components/button"
PLAYERS_TURN_TOPIC = "game/players/{id}/turn"
PLAYERS_HALL_SENSOR_TOPIC = "game/players/{id}/movement"

#########################
# SYNCHRONIZATION FLAGS #
#########################
# Events for coordinating game flow
waitPlayersEvent = Event()
waitDiceEvent = Event()
waitMovementEvent = Event()
waitMinigameElectionEvent = Event()

#######################
# GAME STATE TRACKING #
#######################
# Track current game state and turn
current_state = GameState.WAITING_FOR_PLAYERS
turn = 0
board = DebugBoard() if DEBUG else ClassicBoard()

# Available minigames configuration
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

# Debug mode minigame selection helpers
orderedMinigames: list[MinigameType] = list(sorted(minigames, key=lambda x: x.name))
randomGameDebug: MinigameType = None
minigameIndex: int = 0

##########################
# MQTT MESSAGE HANDLING  #
##########################
def on_message(client, userdata, message):
    """
    Routes MQTT messages to appropriate handlers based on current game state.

    Args:
        client: MQTT client instance
        userdata: User defined data passed to callbacks
        message: Received MQTT message

    Returns:
        None
    """
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

#########################
# GAME STATE MANAGEMENT #
#########################
def setGameState(state: GameState) -> None:
    """
    Updates the current game state and logs the change for debugging.

    Args:
        state: New GameState to set

    Returns:
        None
    """
    global current_state
    utils.printDebug(f"Game state changed to {state.name}")
    current_state = state

######################
# MQTT CLIENT SETUP  #
######################
def createMqttClient(broker: str, port: int, client_id: str) -> mqtt.Client:
    """
    Creates and connects MQTT client with automatic retry logic.

    Args:
        broker: MQTT broker address
        port: MQTT broker port
        client_id: Unique client identifier

    Returns:
        mqtt.Client: Connected MQTT client instance

    Raises:
        ConnectionError: If unable to connect after retries
    """
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    client.on_message = on_message
    print("Connecting to broker...")
    while client.connect(broker, port) != mqtt.MQTT_ERR_SUCCESS:
        print("Connection failed, retrying...")
        time.sleep(1)
    print("Connected!")
    client.loop_start()
    return client

##########################
# PLAYER INITIALIZATION  #
##########################
def waitForPlayers() -> None:
    """
    Initializes player connection phase and waits for all players to connect.
    Subscribes to player connection topics and blocks until all players are ready.

    Returns:
        None
    """
    setGameState(GameState.WAITING_FOR_PLAYERS)
    client.subscribe(PLAYERS_CONNECTION_TOPIC.format(id="+"))
    print("Waiting for players to connect...")
    waitEvent(waitPlayersEvent)
    print("All players connected!")
    time.sleep(2)

def managePlayersConnection(message: mqtt.MQTTMessage) -> None:
    """
    Handles new player connections and initializes their game state.
    
    Args:
        message: MQTT message containing player connection information
        
    Returns:
        None
    """
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
    """
    Processes dice roll button press messages from players.
    
    Args:
        message: MQTT message from player's button press
        
    Returns:
        None
    """
    if message.topic == PLAYERS_BUTTON_TOPIC.format(id=players[turn].id):
        waitDiceEvent.set()

def manageGameElectionManually(message: mqtt.MQTTMessage) -> None:
    """
    Handles manual minigame selection in debug mode.
    Short press cycles through games, long press selects current game.
    
    Args:
        message: MQTT message containing button press type
        
    Returns:
        None
    """
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
    """
    Processes hall sensor triggers during player movement.
    
    Args:
        message: MQTT message from player's hall sensor
        
    Returns:
        None
    """
    if message.topic == PLAYERS_HALL_SENSOR_TOPIC.format(id=players[turn].id):
        waitMovementEvent.set()

def closeMqttConnection(client: mqtt.Client) -> None:
    """
    Cleanly closes MQTT client connection.
    
    Args:
        client: MQTT client instance to close
        
    Returns:
        None
    """
    client.loop_stop()
    client.disconnect()

def initGame() -> None:
    """
    Main game loop that manages turns and overall game flow.
    Handles welcome sequence, player turns, and checks for win conditions.
    Updates game state and player stats after each turn.

    Returns:
        None
    """
    global turn
    setGameState(GameState.PLAYING)
    utils.showInAllLCD(LCDMessage(top="Welcome to".center(16), down="The Game".center(16)))
    utils.playInAllBuzzer(Melodies.GAME_TUNE)
    time.sleep(5)

    while current_state != GameState.GAME_OVER:
        playTurn(players[turn])
        print(players)
        showStats()
        time.sleep(2)
        checkWinner()
        turn = (turn + 1) % NUM_PLAYERS

def checkWinner() -> None:
    """
    Checks if any player has reached winning conditions.
    Updates game state and displays appropriate messages if game is over.
    
    Returns:
        None
    """
    global current_state
    possible_winners = list(filter(lambda player: player.points >= WIN_POINTS, players))
    print(possible_winners)
    if len(possible_winners) == 0:
        return
    setGameState(GameState.GAME_OVER)
    message = None
    if len(possible_winners) == 1:
        winner = possible_winners[0]
        message = LCDMessage(top="Game Over".center(16), down=f"Player {winner.id} wins!".center(16))
    else:
        if possible_winners[0].points == possible_winners[1].points:
            message = LCDMessage(top="Game Over".center(16), down="Draw!".center(16))
        else:
            winner = max(possible_winners, key=lambda player: player.points)
            message = LCDMessage(top="Game Over".center(16), down=f"Player {winner.id} wins!".center(16))

    utils.showInAllLCD(message)
    utils.playInAllBuzzer(Melodies.GAME_OVER_TUNE)
    time.sleep(5)

def playTurn(player: Player) -> None:
    """
    Executes a single player's turn including dice roll, movement, and cell action.

    Args:
        player: Player instance whose turn is being executed

    Returns:
        None
    """
    # Turn phases:
    # 1. Check if turn should be skipped
    # 2. Notify turn start via MQTT
    # 3. Play turn indicators
    # 4. Execute turn actions (roll, move, cell effect)
    # 5. End turn notification

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
    steps = rollDice(player)
    movePlayer(player, steps)
    playCell(player, board.getCellType(player.position))
    client.publish(PLAYERS_TURN_TOPIC.format(id=player.id), 0)

def movePlayer(player: Player, steps: int) -> None:
    """
    Handles player movement including hall sensor detection and position updates.

    Args:
        player: Player to move
        steps: Number of steps to move (positive for forward, negative for backward)

    Returns:
        None
    """
    moveWithHallSensor(player, steps)
    player.moveForward(steps, board.size) if steps > 0 else player.moveBackward(abs(steps), board.size)
    utils.showInLCD(player.id, LCDMessage(top="Moved to".center(16), down=f"cell {player.position}".center(16)))
    utils.showInOtherLCD(
        player.id, LCDMessage(top=f"Player {player.id} moved".center(16), down=f"to cell {player.position}".center(16))
    )
    print(f"Player {player.id} moved to cell {player.position} - {board.getCellName(player.position)}")
    time.sleep(4)

def moveWithHallSensor(player: Player, steps: int) -> None:
    """
    Manages physical movement detection using hall sensor.
    Shows movement instructions and waits for sensor triggers.
    
    Args:
        player: Player who is moving
        steps: Number of steps to detect
        
    Returns:
        None
    """
    setGameState(GameState.MOVING)
    client.subscribe(PLAYERS_HALL_SENSOR_TOPIC.format(id=player.id))

    for i in range(abs(steps), 0, -1):
        utils.showInLCD(player.id, LCDMessage(top="Move the meeple.".center(16), down=f"{i} moves left".center(16)))
        utils.showInOtherLCD(
            player.id, LCDMessage(top=f"P{player.id} moving.".center(16), down=f"{i} moves left".center(16))
        )
        waitEvent(waitMovementEvent)
        # Play the sound of the movement
        utils.playInAllBuzzer(Melodies.MOVE_SOUND)

    client.unsubscribe(PLAYERS_HALL_SENSOR_TOPIC.format(id=player.id))

def rollDice(player) -> int:
    """
    Handles dice rolling mechanics including UI feedback.
    
    Args:
        player: Player whose turn it is to roll
        
    Returns:
        int: Result of the dice roll (1-6)
    """
    setGameState(GameState.ROLLING_DICE)

    topic = PLAYERS_BUTTON_TOPIC.format(id=player.id)

    message = LCDMessage(top="Roll the dice".center(16), down="Press the button".center(16))
    utils.showInLCD(player.id, message)

    client.subscribe(topic)
    waitEvent(waitDiceEvent)
    client.unsubscribe(topic)
    result = Random().randint(1, 6)

    utils.showInLCD(player.id, LCDMessage(top="Dice rolled".center(16), down=str(result).center(16)))
    utils.showInOtherLCD(
        player.id, LCDMessage(top=f"Player {player.id}".center(16), down=f"rolled {result}".center(16))
    )
    time.sleep(4)
    return result

def waitEvent(event: Event) -> bool:
    """
    Waits for an event to be set and clears it afterward.
    
    Args:
        event: Threading Event to wait for
        
    Returns:
        bool: True if event was set, False if timeout occurred
    """
    res = event.wait()
    event.clear()
    return res

def playCell(player: Player, cell_type: CellType) -> None:
    """
    Executes the effect of landing on a specific cell type.
    
    Args:
        player: Player who landed on the cell
        cell_type: Type of cell landed on
        
    Returns:
        None
    """
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
    """
    Handles gaining points cell effect with UI feedback.
    Awards 5-10 random points to the player.
    
    Args:
        player: Player who gained points
        
    Returns:
        None
    """
    utils.playInAllBuzzer(Melodies.GAIN_POINTS_TUNE)
    messagePlayer = LCDMessage(top="Gain Points".center(16))
    utils.showInLCD(player.id, messagePlayer)
    utils.showInOtherLCD(
        player.id, LCDMessage(top=f"Player {player.id} landed".center(16), down="on Gain Points".center(16))
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
    """
    Handles losing points cell effect with UI feedback.
    Deducts 1-5 random points from the player.
    
    Args:
        player: Player who lost points
        
    Returns:
        None
    """
    utils.playInAllBuzzer(Melodies.LOSE_POINTS_TUNE)
    messagePlayer = LCDMessage(top="Lose Points".center(16))
    utils.showInLCD(player.id, messagePlayer)
    utils.showInOtherLCD(
        player.id, LCDMessage(top=f"Player {player.id} landed".center(16), down="on Lose Points".center(16))
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
    """
    Handles skip turn cell effect with UI feedback.
    Marks player to skip their next turn.
    
    Args:
        player: Player who will skip next turn
        
    Returns:
        None
    """
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
    """
    Handles random event cell effect with animation and sound feedback.
    Randomly selects from available events with equal probability.
    
    Args:
        player: Player who triggered the random event
        
    Returns:
        None
    """
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
        player.id, LCDMessage(top=f"Player {player.id} landed".center(16), down="on Random Event".center(16))
    )
    time.sleep(4)

    # Selection animation
    animateOptions(utils, [str(event.value) for event in events])

    # Play the selected event
    playCell(player, random_event)

def moveForward(player: Player) -> None:
    """
    Handles move forward cell effect with UI feedback.
    Moves player 1-3 steps forward and triggers new cell effect.
    
    Args:
        player: Player to move forward
        
    Returns:
        None
    """
    utils.playInAllBuzzer(Melodies.MOVE_FORWARD_TUNE)
    utils.showInLCD(player.id, LCDMessage(top="Move Forward".center(16)))
    utils.showInOtherLCD(
        player.id, LCDMessage(top=f"Player {player.id} landed".center(16), down="on Move Forward".center(16))
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

def moveBackward(player: Player) -> None:
    """
    Handles move backward cell effect with UI feedback.
    Moves player 1-3 steps backward and triggers new cell effect.
    
    Args:
        player: Player to move backward
        
    Returns:
        None
    """
    utils.playInAllBuzzer(Melodies.MOVE_BACKWARD_TUNE)
    utils.showInLCD(player.id, LCDMessage(top="Move Backwards".center(16)))
    utils.showInOtherLCD(
        player.id, LCDMessage(top=f"Player {player.id} landed".center(16), down="on Move Backward".center(16))
    )
    time.sleep(4)
    steps = Random().randint(1, 3)
    utils.showInLCD(player.id, LCDMessage(top=f"Move {steps}".center(16), down="steps backwards".center(16)))
    utils.showInOtherLCD(
        player.id, LCDMessage(top=f"Player {player.id} moves".center(16), down=f"{steps} steps back".center(16))
    )
    time.sleep(4)
    movePlayer(player, -steps)
    playCell(player, board.getCellType(player.position))

def deathEvent(player: Player) -> None:
    """
    Handles death event cell effect with UI feedback.
    Player loses all accumulated points.
    
    Args:
        player: Player who triggered death event
        
    Returns:
        None
    """
    utils.playInAllBuzzer(Melodies.DEATH_TUNE)
    message = LCDMessage(top="Death Event".center(16))
    utils.showInLCD(player.id, message)
    utils.showInOtherLCD(
        player.id, LCDMessage(top=f"Player {player.id} landed".center(16), down="on Death Event".center(16))
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
    """
    Displays current game statistics on all LCD screens.
    Shows points for all players.
    
    Returns:
        None
    """
    message = LCDMessage(
        top=f"P{players[0].id}: {players[0].points} points",
        down=f"P{players[1].id}: {players[1].points} points",
    )
    utils.showInAllLCD(message)
    time.sleep(3)

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
    """
    Initiates and manages a random minigame sequence.
    Handles minigame selection, execution, and winner resolution.
    
    Returns:
        None
    """
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
    """
    Selects a random minigame with animation feedback.
    Uses manual selection in debug mode.
    
    Returns:
        MinigameType: Selected minigame type
    """
    game: MinigameType = None
    if DEBUG:
        game = waitForMinigameElection()
    else:
        # Animate the minigame selection
        minigame_names = [str(game.name).replace("_", " ") for game in minigames.keys()]
        animateOptions(utils, minigame_names)
        game = Random().choice(list(minigames.keys()))
    return game

def waitForMinigameElection() -> MinigameType:
    """
    Waits for the election of a minigame by subscribing to a player's button topic 
    It sets the game state to MINIGAME_ELECTION, and waits for the minigame election event. 
    After the event is received, it unsubscribes from the player's button topic and returns the 
    selected minigame type.

    Returns:
        MinigameType: The type of the randomly selected minigame.
    """
    global randomGameDebug
    global orderedMinigames
    client.subscribe(PLAYERS_BUTTON_TOPIC.format(id=players[turn].id))
    utils.showInAllLCD(LCDMessage(top=orderedMinigames[0].name.center(16)))
    setGameState(GameState.MINIGAME_ELECTION)
    waitEvent(waitMinigameElectionEvent)
    client.unsubscribe(PLAYERS_BUTTON_TOPIC.format(id=players[turn].id))
    return randomGameDebug

def handleWinners(winners: list[Player], winning_points: int) -> None:
    """
    Handles the outcome of a game by processing the winners and providing feedback.
    Args:
        winners (list[Player]): A list of Player objects who have won the game.
        winning_points (int): The number of points awarded to the winners.
    Returns:
        None
    """
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

#################
# MAIN PROGRAM #
#################
if __name__ == "__main__":
    """
    Main program entry point with error handling and cleanup.
    Initializes MQTT client, waits for players, and starts game loop.
    Ensures proper cleanup on exit.
    """
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
