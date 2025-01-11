from enum import Enum

class GameState(Enum):
    """
    Enumeration of all possible game states.
    Controls game flow and determines valid actions at each stage.
    """
    WAITING_FOR_PLAYERS = 0    # Initial state waiting for player connections
    PLAYING = 1               # Normal gameplay state
    ROLLING_DICE = 2         # Waiting for dice roll input
    GAME_OVER = 3            # Game has ended
    MINIGAME = 4             # Currently playing a minigame
    MINIGAME_ELECTION = 5    # Selecting a minigame (debug mode)
    MOVING = 6               # Player is moving their piece
