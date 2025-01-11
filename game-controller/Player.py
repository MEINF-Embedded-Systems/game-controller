
class Player:
    """
    Represents a player in the game with their state and capabilities.
    Manages player position, points, and status effects.
    """
    
    def __init__(self, id: int) -> None:
        """
        Initialize a new player.

        Args:
            id: Unique player identifier
        """
        self.id = id
        self.points = 0
        self.connected = False
        self.position = 0
        self.skipped = False

    def __str__(self) -> str:
        """
        String representation of player state.
        
        Returns:
            str: Formatted player information
        """
        return f"Player {self.id} - Points: {self.points} - Connected: {self.connected}"

    def gainPoints(self, points: int) -> None:
        """
        Add points to player's score.
        
        Args:
            points: Number of points to add
        """
        self.points += points

    def losePoints(self, points: int) -> None:
        """
        Remove points from player's score, minimum 0.
        
        Args:
            points: Number of points to remove
        """
        self.points -= points
        if self.points < 0:
            self.points = 0

    def moveForward(self, steps: int, board_size: int) -> None:
        """
        Move player forward on board with wraparound.
        
        Args:
            steps: Number of spaces to move
            board_size: Total number of board spaces
        """
        self.position = (self.position + steps) % board_size

    def moveBackward(self, steps: int, board_size: int) -> None:
        """
        Move player backward on board with wraparound.
        
        Args:
            steps: Number of spaces to move
            board_size: Total number of board spaces
        """
        self.position = (self.position - steps) % board_size

    def __eq__(self, value):
        """
        Compare players by ID.
        
        Args:
            value: Other player to compare with
            
        Returns:
            bool: True if players have same ID
        """
        return self.id == value.id
