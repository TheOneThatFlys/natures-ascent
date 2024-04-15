import pygame

from .element import Element
from .style import Style

class Text(Element):
    def __init__(self, parent: Element, style: Style, text: str = "") -> None:
        self.text = text
        super().__init__(parent, style)

    def set_text(self, text: str) -> None:
        self.text = text
        self.redraw_image()

    def redraw_image(self) -> None:
        self.image = self.style.font.render(self.text, False, self.style.fore_colour)

        if self.style.text_shadow:
            base_img = pygame.Surface((self.image.get_width() + self.style.text_shadow, self.image.get_height() + self.style.text_shadow), pygame.SRCALPHA)
            shadow_image = self.style.font.render(self.text, False, self.style.colour)

            base_img.blit(shadow_image, (0, self.style.text_shadow))
            base_img.blit(self.image, (0, 0))
            self.image = base_img

        self.rect = self.image.get_rect()
        self.calculate_position()