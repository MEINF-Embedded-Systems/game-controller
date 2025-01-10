from CellType import CellType
from boards import Board


class DebugBoard(Board):
    def __init__(self):
        super().__init__()
        # self.size = 9
        # self.cells = [
        #     CellType.ST,
        #     CellType.GP,
        #     CellType.LP,
        #     CellType.MG,
        #     CellType.RE,
        #     CellType.DE,
        #     CellType.SK,
        #     CellType.MF,
        #     CellType.MB,
        # ]
        self.size = 2
        self.cells = [
            CellType.RE,
            CellType.MG,
        ]
