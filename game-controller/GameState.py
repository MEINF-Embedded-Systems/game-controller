from enum import Enum


class GameState(Enum):
    WAITING_FOR_PLAYERS = 0
    PLAYING = 1
    ROLLING_DICE = 2
    GAME_OVER = 3
    MINIGAME = 4
