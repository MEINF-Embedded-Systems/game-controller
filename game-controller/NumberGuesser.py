from AbstractMinigame import Minigame

class NumberGuesser(Minigame):
    def __init__(self, num_players: int) -> None:
        super().__init__(num_players)
        self.number = 0
        self.players = [False] * num_players
        self.current_player = 0

    def handleMQTTMessage(self, message: str) -> None:
        if message == "start":
            self.number = 5
            self.players = [False] * self.num_players
            self.current_player = 0
            self.players[self.current_player] = True
        elif message == "higher":
            self.number += 1
        elif message == "lower":
            self.number -= 1
        elif message == "correct":
            self.players[self.current_player] = False
            self.current_player = (self.current_player + 1) % self.num_players
            self.players[self.current_player] = True

    def isFinished(self) -> bool:
        return not any(self.players)
    
    def getWinner(self) -> int:
        return self.current_player