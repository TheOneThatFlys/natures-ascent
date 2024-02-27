import pygame

from .element import Element
from .style import Style

class Text(Element):
    def __init__(self, parent, style: Style, text: str = ""):
        self.text = text
        super().__init__(parent, style)

    def set_text(self, text: str):
        self.text = text
        self.redraw_image()

    def redraw_image(self):
        self.image = self.style.font.render(self.text, False, self.style.fore_colour)
        self.rect = self.image.get_rect()
        self.calculate_position()