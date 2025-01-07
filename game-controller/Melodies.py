from Message import BuzzerMessage

GAME_TUNE = None

WINNING_SOUND = BuzzerMessage(tones=[262, 294, 330, 349, 392, 0], duration=[150] * 5)

LOSING_SOUND = BuzzerMessage(tones=[392, 349, 330, 294, 262, 0], duration=[200] * 4 + [400])
