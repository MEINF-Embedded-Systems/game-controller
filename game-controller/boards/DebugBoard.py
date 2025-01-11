from CellType import CellType
from boards import Board


class DebugBoard(Board):
    def __init__(self):
        super().__init__()
        self.size = 12
        self.cells = [
            CellType.ST,
            CellType.ST,
            CellType.GP,
            CellType.GP,
            CellType.LP,
            CellType.LP,
            CellType.MG,
            CellType.MG,
            CellType.RE,
            CellType.RE,
            CellType.DE,
            CellType.DE,
            # CellType.MF,
            # CellType.MB,
        ]
        # self.size = 2
        # self.cells = [
        #     CellType.RE,
        #     CellType.MG,
        # ]
