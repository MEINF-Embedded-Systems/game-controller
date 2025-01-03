# Initialize package
# Import submodules
from .AbstractMinigame import Minigame
from .MinigameType import MinigameType
from .NumberGuesser import NumberGuesser

# Define __all__ to control * imports
__all__ = ["Minigame", "MinigameType", "NumberGuesser"]