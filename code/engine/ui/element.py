import pygame
from ..node import Node
from .style import Style

class Element(Node):
    def __init__(self, parent: Node, style: Style):
        super().__init__(parent)

        if hasattr(parent, "style"):
            parent_style = parent.style
        else:
            parent_style = Style()

        self.style = Style.merge(parent_style, style)

        self.redraw_image()

    def calculate_position(self):
        "Moves element rect based on style"
        if self.style.position == "relative":
            base_rect = self.parent.rect
        elif self.style.position == "absolute":
            raise NotImplementedError()
        else:
            raise TypeError(f"Unknown position type: {self.style.position}")

        y_alignment, x_alignment = self.style.alignment.split("-")
        if x_alignment == "left":
            self.rect.x = base_rect.x + self.style.offset[0]
        elif x_alignment == "right":
            self.rect.right = base_rect.right - self.style.offset[0]
        elif x_alignment == "center":
            self.rect.centerx = base_rect.centerx + self.style.offset[0]

        if y_alignment == "top":
            self.rect.y = base_rect.y + self.style.offset[1]
        elif y_alignment == "bottom":
            self.rect.bottom = base_rect.bottom - self.style.offset[1]
        elif y_alignment == "center":
            self.rect.centery = base_rect.centery + self.style.offset[1]

    def redraw_image(self):
        self.image = pygame.Surface(self.style.size)
        self.image.fill(self.style.colour)

        if self.style.image:
            # if no size provided
            if self.style.size == (0, 0):
                self.image = self.style.image

            else:
                if self.style.stretch_type == "none":
                    self.image.blit(self.style.image, (0, 0))
                elif self.style.stretch_type == "expand":
                    # enlarge the image to the biggest it can fit inside element
                    # without distorting it
                    x_factor = self.image.get_width() / self.style.image.get_width()
                    y_factor = self.image.get_height() / self.style.image.get_height()
                    scale_factor = min(x_factor, y_factor)

                    self.image.blit(pygame.transform.scale(self.style.image, (self.style.image.get_width() * scale_factor, self.style.image.get_height() * scale_factor)), (0, 0))
                elif self.style.stretch_type == "skew":
                    # expand the image to fit the bounds
                    self.image = pygame.transform.scale(self.style.image, self.style.size)
                elif self.style.stretch_type == "fit":
                    # image is native resolution
                    self.image = self.style.image
                else:
                    raise TypeError(f"Unknown image stretch type: {self.style.stretch_type}")

        self.rect = self.image.get_rect()
        self.calculate_position()

    def set_style(self, new_style: Style):
        if self.style != new_style:
            self.style = new_style
            self.redraw_image()

    def render(self, window):
        # draw self then render children
        if self.style.visible:
            window.blit(self.image, self.rect)

        for child in self.children:
            child.render(window)

    def update(self):
        for child in self.children:
            child.update()