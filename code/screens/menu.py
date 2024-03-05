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
                image = self.manager.get_image("bg"),
                stretch_type = "skew"
            )
        )

        self.title = self.master_container.add_child(
            Text(
                parent = self.master_container,
                text = "Nature's Ascent",
                style = Style(
                    alignment = "top-center",
                    offset = (0, 100),
                    fore_colour = (255, 255, 255),
                    font = self.manager.get_font("alagard", 72),
                )
            )
        )

        self.play_button = self.master_container.add_child(
            Button(
                parent = self.master_container,
                style = Style(
                    alignment = "top-center",
                    offset = (0, 200),
                    size = (120, 70),
                    colour = (0, 255, 0),
                    image = self.manager.get_image("download"),
                    stretch_type = "skew",
                ),
                hover_style = Style(
                    colour = (255, 0, 0),
                    image = None,
                ),
                on_click = self.parent.set_screen,
                click_args = ("level",),
            )
        )

        self.play_button.add_child(
            Text(
                parent = self.play_button,
                text = "Play",
                style = Style(
                    alignment = "center-center",
                    fore_colour = (255, 255, 255),
                    font = self.manager.get_font("alagard", 24),
                    offset = (0.1, 0),
                )
            )
        )

    def render(self, window):
        self.master_container.render(window)

    def update(self):
        self.master_container.update()