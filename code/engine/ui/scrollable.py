import pygame

from typing import TypeVar

from engine.types import *

from .element import Element
from .style import Style

class ScrollableElement(Element):
    def __init__(self, parent: Element, style: Style, scroll_factor: float = 1.0, focus_only: bool = True) -> None:
        super().__init__(parent, style)
        self.scroll_factor = scroll_factor
        self.focus_only = focus_only

        self._scroll_amount = 0

        self._scroll_min = -999999
        self._scroll_max = 0

        self._calculate_scroll_bounds()

    def _calculate_scroll_bounds(self) -> None:
        lowest_point = max([child.rect.bottom for child in self.get_all_children()])
        self._scroll_min = -(lowest_point - self.rect.bottom) - 4

    T = TypeVar("T")
    def add_child(self, child: T) -> T:
        a = super().add_child(child)
        self._calculate_scroll_bounds()
        return a

    def on_scroll(self, dx: int, dy: int) -> None:
        super().on_scroll(dx, dy)

        if not self.focus_only or self.rect.collidepoint(self.manager.get_mouse_pos()):
            change = dy * self.scroll_factor
            if self._scroll_amount + change < self._scroll_min:
                change = self._scroll_min - self._scroll_amount
            if self._scroll_amount + change > self._scroll_max:
                change = self._scroll_max - self._scroll_amount
            self._scroll_amount += change

            for child in self.get_all_children()[1:]:
                child.rect.y += change

    def on_resize(self, new_res: Vec2) -> None:
        super().on_resize(new_res)
        for child in self.get_all_children()[1:]:
                child.rect.y += self._scroll_amount
        self._calculate_scroll_bounds()

    def render(self, surface: pygame.Surface) -> None:
        blacklisted = []
        for child in self.get_all_children():
            if child.rect.top < self.rect.bottom and child.rect.bottom > self.rect.top and child.style.alpha > 0:
                if not child.style.visible or child.parent in blacklisted:
                    blacklisted.append(child)
                    continue

                if child.rect.top < self.rect.top:
                    upper_cutoff = self.rect.top - child.rect.top
                    image = pygame.Surface((child.rect.width, child.rect.height - upper_cutoff), pygame.SRCALPHA)
                    image.blit(child.image, (0, -upper_cutoff))
                    surface.blit(image, (child.rect.x, self.rect.y))
                elif child.rect.bottom > self.rect.bottom:
                    lower_cutoff = child.rect.bottom - self.rect.bottom
                    image = pygame.Surface((child.rect.width, child.rect.height - lower_cutoff), pygame.SRCALPHA)
                    image.blit(child.image, (0, 0))
                    surface.blit(image, (child.rect.x, self.rect.bottom - image.get_height()))
                else:
                    surface.blit(child.image, child.rect)