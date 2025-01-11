from enum import Enum

class CellType(Enum):
    """
    Enumeration of possible board cell types.
    Each type triggers different game effects when landed on.
    """
    ST = "Start"             # Starting position
    GP = "Gain Points"       # Player gains points
    LP = "Lose Points"       # Player loses points
    MF = "Move Forward"      # Move additional spaces forward
    MG = "MiniGame"         # Trigger a minigame
    MB = "Move Backward"    # Move spaces backward
    DE = "Death"            # Lose all points
    SK = "Skip Turn"        # Skip next turn
    RE = "Random Event"     # Random effect occurs
