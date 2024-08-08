import pygame
import os, base64
from typing import Literal

from engine import Node, Logger

def parse_spritesheet(spritesheet: pygame.Surface, *, frame_count: int = None, frame_size: tuple[int, int] = None, direction: Literal["x", "y"] = "x") -> list[pygame.Surface]:
    """
    Returns a list of surfaces containing each frame of the sprite sheet.

    Modifications to the base spritesheet will not affect the resulting frames.
    """

    if direction != "x" and direction != "y":
        raise TypeError(f"Function parse_spritesheet passed unknown direction parameter: {direction}")

    if frame_size == None and frame_count == None:
        raise TypeError("Function parse_spritesheet must include a frame_count or frame_size parameter.")
    
    if frame_count:
        n = frame_count

        width = spritesheet.get_width() / frame_count if direction == "x" else spritesheet.get_width()
        height = spritesheet.get_height() / frame_count if direction == "y" else spritesheet.get_height()
    else:
        if direction == "x":
            n = spritesheet.get_width() // frame_size[0]
        else:
            n = spritesheet.get_height() // frame_size[1]

        width, height = frame_size

    frames = []
    for i in range(n):
        frame = pygame.Surface((width, height), pygame.SRCALPHA)

        x_offset = -i * width if direction == "x" else 0
        y_offset = -i * height if direction == "y" else 0

        frame.blit(spritesheet, (x_offset, y_offset))

        frames.append(frame)

    return frames

class SaveHelper:
    @staticmethod
    def encode_data(data: bytes) -> str:
        return str(base64.b85encode(data))[2:-1]

    @staticmethod
    def decode_data(data: str) -> bytes:
        return base64.b85decode(data)

    @staticmethod
    def save_file(data: str | bytes, filepath: str, obfuscate: bool = False) -> None:
        """Save a file with string data"""
        # create all folders in path if they don't already exists

        accumulated_path = ""
        for folder in os.path.dirname(filepath).split(os.path.sep):
            accumulated_path += folder
            if not os.path.exists(accumulated_path):
                os.mkdir(accumulated_path)
        
        data_to_save = SaveHelper.encode_data(data) if obfuscate else data
        with open(filepath, "wb" if isinstance(data_to_save, bytes) else "w") as f:
            f.write(data_to_save)

    @staticmethod
    def load_file(filepath: str, obfuscated: bool = False, format: Literal["bytes", "text"] = "text") -> str | bytes | None:
        """Read a file as string. Returns none if file does not exist"""
        if os.path.exists(filepath):
            with open(filepath, "rb" if format == "bytes" else "r") as f:
                loaded_data = f.read()
            return SaveHelper.decode_data(loaded_data) if obfuscated else loaded_data
        return None
    
class AutoSaver(Node):
    """Class for creating auto saved files. Make sure to update ``AutoSaver.data`` in order for saved data to be up to date."""
    MIN_INTERVAL = 1800 # 30 seconds
    def __init__(self, parent: Node, filepath: str, interval: int, **kwargs) -> None:
        super().__init__(parent)
        self.filepath = filepath
        self.interval = interval
        self._counter = 0

        self.data: str = ""

        # set time interval to the minimum set if too low
        if kwargs.get("ignore_limit", False) == False and interval < AutoSaver.MIN_INTERVAL:
            Logger.warn(f"Autosave interval for {filepath} set too low. Defaulting to minimum {AutoSaver.MIN_INTERVAL}. Set 'ignore_limit' kwarg to True in order to ignore this limit.")
            self.interval = AutoSaver.MIN_INTERVAL

    def force_save(self) -> None:
        """Save data to file now. Restarts timer to next save."""
        SaveHelper.save_file(self.data, self.filepath)
        self.interval = 0

    def update(self) -> None:
        self._counter += self.manager.dt
        if self._counter > self.interval:
            SaveHelper.save_file(self.data, self.filepath)
            self._counter = 0