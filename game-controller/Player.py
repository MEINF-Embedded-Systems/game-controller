# Player class with id, points and connection status
class Player:
    def __init__(self, id: int) -> None:
        self.id = id
        self.points = 0
        self.connected = False
        self.position = 0

    def __str__(self) -> str:
        return f"Player {self.id} - Points: {self.points} - Connected: {self.connected}"

    def gainPoints(self, points: int) -> None:
        self.points += points

    def losePoints(self, points: int) -> None:
        self.points -= points
        if self.points < 0:
            self.points = 0

    def moveForward(self, steps: int, board_size: int) -> None:
        self.position = (self.position + steps) % board_size

    def moveBackward(self, steps: int, board_size: int) -> None:
        self.position = (self.position - steps) % board_size

    def __eq__(self, value):
        return self.id == value.id
