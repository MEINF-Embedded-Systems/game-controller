from enum import Enum


class CellType(Enum):
    ST = "Start"
    GP = "Gain Points"
    LP = "Lose Points"
    MF = "Move Forward"
    MG = "MiniGame"
    MB = "Move Backward"
    DE = "Death"
    SK = "Skip Turn"
    RE = "Random Event"
