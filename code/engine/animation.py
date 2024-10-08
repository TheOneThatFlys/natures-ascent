from __future__ import annotations

import pygame
from util.constants import *
from .node import Node
from .sprite import Sprite

class AnimationManager(Node):
    """
    Component for adding animations to a sprite.
    """
    def __init__(self, parent: Sprite, frame_time = ANIMATION_FRAME_TIME) -> None:
        super().__init__(parent)
        self._animations: dict[str, list[pygame.Surface]] = {}
        self._current = ""

        self._frame_time = frame_time
        self._counter = 0
        self._current_index = 0

        self.finished = False
        self.played_once = False

    def _recenter_parent(self) -> None:
        # recalculate parent offset so its centered
        if self._current != "": # prevent first frame bugs
            rect_size = self.parent.rect.size
            this_size = self._animations[self._current][0].get_size()

            change = this_size[0] - rect_size[0], this_size[1] - rect_size[1]
            self.parent.render_offset = (-change[0] / 2, -change[1] / 2)

    @property
    def current(self) -> str:
        return self._current

    def add_animation(self, key: str, animation: list[pygame.Surface]) -> AnimationManager:
        """Add an animation. Can be chain called."""
        self._animations[key] = animation
        return self

    def set_animation(self, key: str) -> pygame.Surface:
        """Plays the specified animation and returns first frame."""
        self._current = key
        self._current_index = 0
        self.finished = False
        self.played_once = False
        # reset frame cooldown so no latency
        # when swapping animations
        self._counter = self._frame_time

        return self._animations[key][0]

    def get_animation(self, key: str) -> list[pygame.Surface]:
        return self._animations[key]
    
    def rotate_animation(self, key: str, angle: float) -> None:
        """Rotate an animation by a given angle in degrees, anti-clockwise."""
        self._animations[key] = [pygame.transform.rotate(frame, angle) for frame in self._animations[key]]

    def get_current_frame(self) -> pygame.Surface:
        return self._animations[self._current][self._current_index]

    def update(self) -> None:
        self._counter += self.manager.dt
        if not self.finished and self._counter >= self._frame_time - 1: 
            if self._current_index == 0 and self.played_once:
                self.finished = True
                
        if self._counter >= self._frame_time:
            self.parent.image = self._animations[self._current][self._current_index]
            self._recenter_parent()

            self._current_index += 1

            self._counter = 0
            if self._current_index == len(self._animations[self._current]):
                self._current_index = 0
                self.played_once = True

