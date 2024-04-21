import pygame
import os, base64
from typing import Literal

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
        return str(base64.b64encode(data))[2:-1]

    @staticmethod
    def decode_data(data: str) -> bytes:
        return base64.b64decode(data)

    @staticmethod
    def save_file(data: str | bytes, filename: str, obfuscate: bool = False) -> None:
        """Save a file with string data. Creates save folder if none exists"""
        data_to_save = SaveHelper.encode_data(data) if obfuscate else data

        path = os.path.join("saves", filename)
        if not os.path.exists("saves"):
            os.mkdir("saves")
        with open(path, "w") as f:
            f.write(data_to_save)

    @staticmethod
    def load_file(filename: str, obfuscated: bool = False) -> str | bytes | None:
        """Read a file as string. Returns none if file does not exist"""
        path = os.path.join("saves", filename)
        if os.path.exists(path):
            with open(path, "r") as f:
                loaded_data = f.read()
            return SaveHelper.decode_data(loaded_data) if obfuscated else loaded_data
        return None