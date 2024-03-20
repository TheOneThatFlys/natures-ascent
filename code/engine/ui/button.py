import pygame
from typing import Iterable, Callable
from .element import Element
from .style import Style

class Button(Element):
    def __init__(self, parent, style: Style, hover_style, on_click: Callable[..., None] = None, click_args: Iterable = []):
        super().__init__(parent, style)

        self.normal_style = self.style
        self.hover_style = Style.merge(self.style, hover_style)

        # add dummy function that does nothing if no click event set
        self.on_click = on_click if on_click else self.do_nothing
        self.click_args = click_args

        self.hovering = False
        self.last_hovering = self.hovering
        self.clicking = False
        self._prev_frame_click = False

    def do_nothing(self):
        pass # do nothing

    def update(self):
        super().update()

        mouse_pos = pygame.mouse.get_pos()
        left_clicking = pygame.mouse.get_pressed()[0]
        self.last_hovering = self.hovering
        self.clicking = False
        self.hovering = False

        if self.rect.collidepoint(mouse_pos):
            self.hovering = True
            self.set_style(self.hover_style)
            self.manager.set_cursor("cursor/hand")

            if left_clicking:
                self.clicking = True
                if not self._prev_frame_click:
                    self.on_click(*self.click_args)

        else:
            self.set_style(self.normal_style)

        self._prev_frame_click = left_clicking
        