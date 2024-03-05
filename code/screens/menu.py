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
                colour = (23, 24, 25)
            )
        )

        self.title = self.master_container.add_child(
            Text(
                parent = self.master_container,
                text = "Nature's Ascent",
                style = Style(
                    alignment = "top-center",
                    offset = (0, 100),
                    fore_colour = (99, 169, 65),
                    font = self.manager.get_font("alagard", 72),
                )
            )
        )

        self.tree_img = self.master_container.add_child(
            Element(
                self,
                style = Style(
                    size = (384, 384),
                    image = self.manager.get_image("tree"),
                    stretch_type = "expand",
                    alignment = "bottom-center"
                )
            )
        )

        self.play_button = self.master_container.add_child(
            Button(
                parent = self.master_container,
                style = Style(
                    alignment = "bottom-center",
                    offset = (0, self.tree_img.image.get_height() + 48),
                    size = (192, 96),
                    image = self.manager.get_image("play_button/normal"),
                    stretch_type = "expand",
                ),
                hover_style = Style(
                    image = self.manager.get_image("play_button/hover"),
                ),
                on_click = self.parent.set_screen,
                click_args = ("level",),
            )
        )

        # play button text
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