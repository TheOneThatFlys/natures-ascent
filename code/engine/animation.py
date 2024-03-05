import pygame
from .node import Node
from .sprite import Sprite

def parse_spritesheet(spritesheet, *, frame_size: tuple[int, int] = None, frame_count: int = None, no_alpha: bool = False, flip: bool = False) -> list[pygame.Surface]:
    """
    Returns a list of surfaces containing each frame of the sprite sheet.

    Modifications to the base spritesheet will not affect the resulting frames.

    Only needs one of either frame_count or frame_size parameters.

    Spritesheet must contain each frame horizontally with no padding.
    """

    if frame_count != None:
        n = frame_count
        size = (spritesheet.get_width() / frame_count, spritesheet.get_height())
    elif frame_size != None:
        n = spritesheet.get_width() // frame_size[0]
        size = frame_size
    else:
        raise TypeError("Function parse_animation missing either parameter: frame_size or frame_count")

    frames = []
    for i in range(n):
        if no_alpha:
            frame = pygame.Surface(size)
        else:
            frame = pygame.Surface(size, pygame.SRCALPHA)
        frame.blit(spritesheet, (-i * size[0], 0))
        if flip:
            frame = pygame.transform.flip(frame, 1, 0)
        frames.append(frame)

    return frames

class AnimationManager(Node):
    """
    Component for adding animations to a sprite.
    """
    def __init__(self, parent: Sprite, frame_time = 10):
        super().__init__(parent)
        self._animations: dict[str, list[pygame.Surface]] = {}
        self._current = ""

        self._frame_time = frame_time
        self._counter = 0
        self._current_index = 0

    def add_animation(self, key: str, animation: list[pygame.Surface]):
        "Add an animation. Can be chain called."
        self._animations[key] = animation
        return self

    def set_animation(self, key: str):
        "Plays the specified animation and returns first frame."
        if key != self._current:
            self._current = key
            self._current_index = 0

        return self._animations[key][0]

    def update(self):
        self._counter += self.manager.dt
        if self._counter >= self._frame_time:
            self.parent.image = self._animations[self._current][self._current_index]
            self._current_index += 1
            if self._current_index == len(self._animations[self._current]):
                self._current_index = 0
            self._counter = 0

