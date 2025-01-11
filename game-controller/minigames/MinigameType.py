from enum import Enum

class MinigameType(Enum):
    """
    Defines the available types of minigames in the system.
    Each enum value corresponds to a specific minigame implementation.
    """
    Hot_Potato = 1          # Pass a virtual hot potato before time runs out
    Blind_Timer = 2         # Try to stop a timer at the right moment
    Number_Guesser = 3      # Guess a hidden number without going over
    Tug_of_War = 4          # Pull a virtual rope to your
    Rock_Paper_Scissors = 5
    Last_Stick_Standing = 6
    Quick_Reflexes = 7
