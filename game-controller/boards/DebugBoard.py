from CellType import CellType
from boards import Board


class DebugBoard(Board):
    def __init__(self):
        super().__init__()
        # self.cells = [
        #     CellType.ST,
        #     CellType.GP,
        #     CellType.LP,
        #     CellType.MG,
        #     CellType.RE,
        #     CellType.DE,
        #     # CellType.MF,
        #     # CellType.MB,
        # ]
        self.cells = [
            CellType.ST,
            # CellType.MF,
            # CellType.MB,
        ]
        self.size = len(self.cells)
