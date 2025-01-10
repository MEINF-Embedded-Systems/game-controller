from Message import BuzzerMessage

GAME_TUNE = BuzzerMessage(
    tones=[262, 330, 392, 523, 392, 330, 262, 392, 0],
    duration=[150, 150, 150, 300, 150, 150, 150, 300],
)

WINNING_SOUND = BuzzerMessage(tones=[262, 294, 330, 349, 392, 0], duration=[150] * 5)

LOSING_SOUND = BuzzerMessage(tones=[392, 349, 330, 294, 262, 0], duration=[200] * 4 + [400])

SELECTION_SOUND = BuzzerMessage(tones=[440, 523, 659, 784, 880], duration=[100] * 4 + [200])

YOUR_TURN_SOUND = BuzzerMessage(
    tones=[784, 880, 988, 1047, 0], duration=[600, 600, 600, 600, 600]
)
