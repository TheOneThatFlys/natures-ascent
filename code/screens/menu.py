import pygame
from engine import Screen
from engine.ui import Element, Style, Text, Button

class Menu(Screen):
    def __init__(self, parent):
        super().__init__("menu", parent)
        
        self.master_container = Element(
            parent = self,
            style = Style(
                size = self.rect.size,
            )
        )

        self.test_image = self.master_container.add_child(
            Element(
                parent = self.master_container,
                style = Style(
                    alignment = "bottom-center",
                    image = pygame.image.load("assets/download.png").convert(),
                    stretch_type = "fit"
                )
            )
        )

        self.title = self.master_container.add_child(
            Text(
                parent = self.master_container,
                text = "TILE HERE",
                style = Style(
                    alignment = "top-center",
                    offset = (0, 100),
                    fore_colour = (255, 255, 255),
                    font = pygame.font.Font(None, 32),
                )
            )
        )

        self.test_button = self.master_container.add_child(
            Button(
                parent = self.master_container,
                style = Style(
                    alignment = "top-center",
                    offset = (0, 200),
                    size = (120, 70),
                    colour = (0, 255, 0),
                    image = pygame.image.load("assets/download.png").convert(),
                    stretch_type="skew",
                ),
                hover_style = Style(
                    colour = (255, 0, 0),
                ),
                on_click = self.parent.set_screen,
                click_args = ("level",),
            )
        )

        self.test_button.add_child(
            Text(
                parent = self.test_button,
                text = "WOW",
                style = Style(
                    alignment = "center-center",
                    fore_colour = (255, 255, 255),
                    font = pygame.font.Font(None, 16),
                    offset = (0.1, 0),
                )
            )
        )

    def render(self, window):
        self.master_container.render(window)

    def update(self):
        self.master_container.update()