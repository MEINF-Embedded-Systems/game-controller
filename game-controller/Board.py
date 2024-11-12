from CellType import CellType


class Board:
    def __init__(self):
        self.size = 16
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

    def getCellType(self, position: int) -> CellType:
        return self.cells[position]

    def getCellName(self, position: int) -> str:
        return self.cells[position].value
