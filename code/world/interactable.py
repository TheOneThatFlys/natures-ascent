import pygame

from engine import Node, Sprite, Logger
from util.constants import *

class Interactable(Sprite):
    def __init__(self, parent: Node, groups: list[str] = []) -> None:
        super().__init__(parent, groups = ["interact", "render"] + groups)

    def interact(self) -> None:
        """Called when the player interacts with the object"""
        Logger.warn(f"Interact method not implemented for {self.__class__.__name__}.")

    def on_focus(self) -> None:
        """Called when current interact focus is on object."""
        pass

    def on_unfocus(self) -> None:
        """Called when current interact focus is removed from object."""
        pass

class TutorialSign(Interactable):
    def __init__(self, parent: Node, position) -> None:
        super().__init__(parent)
        self.image = pygame.transform.scale_by(self.manager.get_image("tiles/sign"), PIXEL_SCALE)
        self.rect = self.image.get_rect(topleft = position)

        self.key_hint = Sprite(self)
        self.key_hint.image = pygame.Surface((16, 16))
        self.key_hint.image.fill((255, 255, 255))
        self.key_hint.rect = self.key_hint.image.get_rect(centerx = self.rect.centerx, bottom = self.rect.top - 8)
        self.add_child(self.key_hint)

    def interact(self) -> None:
        pass

    def on_focus(self) -> None:
        self.key_hint.add(self.manager.groups["render"])

    def on_unfocus(self) -> None:
        self.key_hint.remove(self.manager.groups["render"])
    