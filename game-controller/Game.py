from GameState import GameState


class Game:

    def __init__(self, board):
        self.board = board
        self.turn = 0
        self.state = GameState.WAITING_FOR_PLAYERS
        
    def setGameState(self, state: GameState) -> None:
        self.state = state
