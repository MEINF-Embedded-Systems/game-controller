from Message import BuzzerMessage

GAME_TUNE = BuzzerMessage(
    tones=[262, 330, 392, 523, 392, 330, 262, 392, 0],
    duration=[150, 150, 150, 300, 150, 150, 150, 300],
)

WINNING_SOUND = BuzzerMessage(tones=[262, 294, 330, 349, 392, 0], duration=[150] * 5)

LOSING_SOUND = BuzzerMessage(tones=[392, 349, 330, 294, 262, 0], duration=[200] * 4 + [400])

SELECTION_SOUND = BuzzerMessage(tones=[440, 523, 659, 784, 880, 0], duration=[100] * 4 + [200])

YOUR_TURN_SOUND = BuzzerMessage(
    tones=[784, 880, 988, 1047, 0], duration=[600, 600, 600, 600]
)

MOVE_SOUND = BuzzerMessage(tones=[880, 440, 0], duration=[50, 100])

TUG_OF_WAR_TUNE = BuzzerMessage(
    tones=[523, 494, 440, 392, 440, 494, 523, 0],  # Tension building tune
    duration=[200, 200, 200, 400, 200, 200, 400]
)

HOT_POTATO_TUNE = BuzzerMessage(
    tones=[523, 587, 659, 698, 784, 698, 659, 587, 0],  # Playful bouncy tune
    duration=[150, 150, 150, 150, 300, 150, 150, 300]
)

LAST_STICK_TUNE = BuzzerMessage(
    tones=[392, 440, 494, 523, 587, 523, 494, 440, 0],  # Mysterious tune
    duration=[200, 200, 200, 200, 400, 200, 200, 400]
)

NUMBER_GUESSER_TUNE = BuzzerMessage(
    tones=[440, 494, 523, 587, 659, 587, 523, 494, 0],  # Playful questioning tune
    duration=[150, 150, 150, 150, 300, 150, 150, 300]
)

# Board cell tunes
GAIN_POINTS_TUNE = BuzzerMessage(
    tones=[523, 659, 784, 988, 0],  # Happy ascending
    duration=[100, 100, 100, 300]
)

LOSE_POINTS_TUNE = BuzzerMessage(
    tones=[523, 494, 440, 392, 0],  # Sad descending
    duration=[100, 100, 100, 300]
)

MOVE_FORWARD_TUNE = BuzzerMessage(
    tones=[392, 440, 494, 523, 587, 0],  # Quick ascending steps
    duration=[100] * 5
)

MOVE_BACKWARD_TUNE = BuzzerMessage(
    tones=[587, 523, 494, 440, 392, 0],  # Quick descending steps
    duration=[100] * 5
)

MINIGAME_CELL_TUNE = BuzzerMessage(
    tones=[523, 659, 523, 659, 784, 0],  # Playful bounce
    duration=[150, 150, 150, 150, 300]
)

DEATH_TUNE = BuzzerMessage(
    tones=[147, 139, 131, 123, 0],  # Deep descending
    duration=[200, 200, 200, 400]
)

SKIP_TURN_TUNE = BuzzerMessage(
    tones=[523, 494, 0, 494, 523, 0],  # Warning pattern
    duration=[200, 200, 100, 200, 200]
)

RANDOM_EVENT_TUNE = BuzzerMessage(
    tones=[523, 659, 784, 659, 523, 784, 659, 523, 0],  # Mystery pattern
    duration=[100] * 8
)
