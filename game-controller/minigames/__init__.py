# Initialize package
# Import submodules
from .AbstractMinigame import Minigame
from .MinigameType import MinigameType
from .NumberGuesser import NumberGuesser
# from .HotPotato import HotPotato
from .TugOfWar import TugOfWar
from .LastStickStanding import LastStickStanding

# Define __all__ to control * imports
__all__ = ["Minigame", "MinigameType", "NumberGuesser","TugOfWar", "LastStickStanding"]