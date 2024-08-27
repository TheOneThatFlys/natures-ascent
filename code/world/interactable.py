import pygame

from engine import Node, Sprite, Logger
from engine.types import *
from util.constants import *
from util import render_multiline

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

class Sign(Interactable):
    def __init__(self, parent: Node, position: Vec2, text: str) -> None:
        super().__init__(parent)
        self.image = pygame.transform.scale_by(self.manager.get_image("tiles/sign"), PIXEL_SCALE)
        self.rect = self.image.get_rect(topleft = position)

        rendered_text = render_multiline(self.manager.get_font("alagard", 16), text, TEXT_WHITE, TILE_SIZE * 3, alignment = "center")

        self.text_box = Sprite(self)
        self.text_box.image = pygame.Surface((rendered_text.get_width() + 8, rendered_text.get_height() + 8))
        self.text_box.rect = self.text_box.image.get_rect(centerx = self.rect.centerx, bottom = self.rect.top - 8)
        self.text_box.z_index = 1
        
        self.text_box.image.fill(UI_ALTBROWN)
        pygame.draw.rect(self.text_box.image, UI_BROWN, self.text_box.image.get_rect(), 2)
        self.text_box.image.blit(rendered_text, rendered_text.get_rect(center = (self.text_box.image.get_width() / 2, self.text_box.image.get_height() / 2)))

        self.add_child(self.text_box)

        self.text_active = False

    def activate_text(self) -> None:
        if not self.text_active:
            self.text_active = True
            self.text_box.add(self.manager.groups["render"])

    def deactivate_text(self) -> None:
        if self.text_active:
            self.text_active = False
            self.text_box.remove(self.manager.groups["render"])

    def interact(self) -> None:
        if self.text_active:
            self.deactivate_text()
        else:
            self.activate_text()

    def on_unfocus(self) -> None:
        self.deactivate_text()
    