from CellType import CellType
from boards import Board


class ClassicBoard(Board):
    def __init__(self):
        super().__init__()
        self.cells = [
            CellType.ST,
            CellType.GP,
            CellType.LP,
            CellType.MF,
            CellType.MG,
            CellType.RE,
            CellType.DE,
            CellType.LP,
            CellType.MB,
            CellType.MG,
            CellType.GP,
            CellType.MF,
            CellType.MB,
            CellType.RE,
            CellType.SK,
            CellType.MG,
        ]
        self.size = len(self.cells)
