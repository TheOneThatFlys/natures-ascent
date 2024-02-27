import pygame
from typing import Iterable, Callable
from .element import Element
from .style import Style

class Button(Element):
    def __init__(self, parent, style: Style, hover_style, on_click: Callable = None, click_args: Iterable = []):
        super().__init__(parent, style)

        self.normal_style = self.style
        self.hover_style = Style.merge(self.style, hover_style)

        self.on_click = on_click
        self.click_args = click_args

    def update(self):
        super().update()

        mouse_pos = pygame.mouse.get_pos()
        left_clicking = pygame.mouse.get_pressed()[0]

        if self.rect.collidepoint(mouse_pos):
            self.set_style(self.hover_style)

            if left_clicking:
                self.on_click(*self.click_args)

        else:
            self.set_style(self.normal_style)
        