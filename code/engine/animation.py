import pygame
from .node import Node
from .sprite import Sprite

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

        self.finished = False

    @property
    def current(self):
        return self._current

    def add_animation(self, key: str, animation: list[pygame.Surface]):
        "Add an animation. Can be chain called."
        self._animations[key] = animation
        return self

    def set_animation(self, key: str):
        "Plays the specified animation and returns first frame."
        if key != self._current:
            self._current = key
            self._current_index = 0
            self.finished = False

        return self._animations[key][0]

    def update(self):
        self._counter += self.manager.dt
        if self._counter >= self._frame_time:
            self.parent.image = self._animations[self._current][self._current_index]
            self._current_index += 1
            if self._current_index == len(self._animations[self._current]):
                self._current_index = 0
                self.finished = True
            self._counter = 0

