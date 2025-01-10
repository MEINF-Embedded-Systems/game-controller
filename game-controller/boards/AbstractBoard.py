from abc import ABC, abstractmethod
from CellType import CellType


class Board(ABC):
    def __init__(self):
        self.size = 1
        self.cells = [CellType.ST]

    @abstractmethod
    def getCellType(self, position: int) -> CellType:
        return self.cells[position]

    @abstractmethod
    def getCellName(self, position: int) -> str:
        return self.cells[position].value
