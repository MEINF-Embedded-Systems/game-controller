import json

class LCDMessage:
    """
    Represents a message to be displayed on an LCD screen.
    Handles formatting and serialization of two-line LCD messages.
    """
    
    def __init__(self, top: str = "", down: str = "", time: int = 0) -> None:
        """
        Initialize LCD message with optional timing.

        Args:
            top: Text for top line of LCD
            down: Text for bottom line of LCD
            time: Display duration in milliseconds
        """
        self.top = top
        self.down = down
        self.time = time

    def __str__(self) -> str:
        """
        String representation of LCD message.
        
        Returns:
            str: Formatted message content
        """
        return f"{self.top.strip()} {self.down.strip()}"

    def toJson(self) -> str:
        """
        Serialize message to JSON format.
        
        Returns:
            str: JSON representation of message
        """
        return json.dumps({"top": self.top, "down": self.down, "time": self.time})
    
class BuzzerMessage:
    """
    Represents a sequence of tones for buzzer output.
    Handles tone sequences and durations for sound effects.
    """
    
    def __init__(self, tones: list[int], duration: list[int]) -> None:
        """
        Initialize buzzer message with tone sequence.

        Args:
            tones: List of frequencies in Hz
            duration: List of durations in milliseconds
        """
        self.tones = tones
        self.duration = duration
        
    def __str__(self) -> str:
        """
        String representation of buzzer sequence.
        
        Returns:
            str: Formatted tone/duration pairs
        """
        return str(list(zip(self.tones, self.duration)))

    def toJson(self) -> str:
        """
        Serialize message to JSON format.
        
        Returns:
            str: JSON representation of message
        """
        return json.dumps({"tones": self.tones, "duration": self.duration})
