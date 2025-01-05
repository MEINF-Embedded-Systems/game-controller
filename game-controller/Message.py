import json


class LCDMessage:
    def __init__(self, top: str = "", down: str = "", time: int = 0) -> None:
        self.top = top
        self.down = down
        self.time = time

    def __str__(self) -> str:
        return f"{self.top.strip()} {self.down.strip()}"

    def toJson(self) -> str:
        return json.dumps({"top": self.top, "down": self.down, "time": self.time})
    
class BuzzerMessage:
    def __init__(self, tones: list[int], duration: list[int]) -> None:
        self.tones = tones
        self.duration = duration
        
    def __str__(self) -> str:
        return str(list(zip(self.tones, self.duration)))

    def toJson(self) -> str:
        return json.dumps({"tones": self.tones, "duration": self.duration})
