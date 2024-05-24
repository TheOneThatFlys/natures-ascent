
import pygame

from engine import Screen
from engine.ui import Element, Style, Text, Button
from engine.types import *
import util

from .common import TextButton, TextButtonColours

class Menu(Screen):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        
        self.master_container = Element(
            parent = self,
            style = Style(
                size = self.rect.size,
                image = util.draw_background(self.rect.size),
                colour = (78, 173, 245)
            )
        )

        self.tree_img = self.master_container.add_child(
            Element(
                self.master_container,
                style = Style(
                    size = (384, 384),
                    image = self.manager.get_image("menu/tree"),
                    stretch_type = "expand",
                    alignment = "bottom-center"
                )
            )
        )

        self.title = self.master_container.add_child(
            Text(
                parent = self.master_container,
                text = "Nature's Ascent",
                style = Style(
                    alignment = "top-center",
                    offset = (0, 64),
                    fore_colour = (99, 169, 65),
                    colour = (23, 68, 41),
                    text_shadow = 2,
                    font = self.manager.get_font("alagard", 72),
                )
            )
        )

        button_colours = TextButtonColours(
            colour = (99, 169, 65),
            colour_shadow = (23, 68, 41),
            hover_colour = (95, 41, 46),
            hover_colour_shadow = (51, 22, 31)
        )

        self.play_button = self.master_container.add_child(TextButton(
            parent = self.master_container,
            yoffset = self.title.rect.bottom + 16,
            text = "New Run",
            on_click = self.parent.set_screen,
            click_args = ["level"],
            colours = button_colours
        ))

        self.leaderboard_button = self.master_container.add_child(TextButton(
            parent = self.master_container,
            yoffset = self.play_button.rect.bottom,
            text = "Leaderboard",
            enabled = False,
            colours = button_colours
        ))

        self.settings_button = self.master_container.add_child(TextButton(
            parent = self.master_container,
            yoffset = self.leaderboard_button.rect.bottom,
            text = "Settings",
            on_click = self.parent.set_screen,
            click_args = ["settings"],
            colours = button_colours
        ))
        
        self.exit_button = self.master_container.add_child(TextButton(
            parent = self.master_container,
            yoffset = self.settings_button.rect.bottom,
            text = "Exit",
            on_click = self.parent.queue_close,
            colours = button_colours
        ))

        self.secret_button = self.tree_img.add_child(Button(
            parent = self.tree_img,
            style = Style(
                size = (8, 8),
                position = "relative",
                alignment = "center-center",
                visible = False
            ),
            hover_style = None,
            on_click = self.parent.set_screen,
            click_args = ["credits"],
            hover_sound = None,
            click_sound = "effect/hit_alt"
        ))

        self.manager.play_sound(sound_name = "music/menu", loop = True)

    def on_resize(self, new_res: Vec2) -> None:
        super().on_resize(new_res)
        self.master_container.style.size = new_res
        self.master_container.style.image = util.draw_background(new_res)
        self.master_container.on_resize(new_res)

    def on_mouse_down(self, button: int) -> None:
        self.master_container.on_mouse_down(button)

    def render(self, window: pygame.Surface) -> None:
        self.master_container.render(window)

    def update(self) -> None:
        self.master_container.update()

class CreditsScreen(Screen):
    def __init__(self, parent) -> None:
        super().__init__(parent)

        self.master_container = Element(
            parent = self,
            style = Style(
                size = self.rect.size,
                image = util.draw_background(self.rect.size),
                colour = (78, 173, 245)
            )
        )

        self.title = self.master_container.add_child(
            Text(
                parent = self.master_container,
                text = "Credits",
                style = Style(
                    alignment = "top-center",
                    offset = (0, 64),
                    fore_colour = (99, 169, 65),
                    colour = (23, 68, 41),
                    text_shadow = 2,
                    font = self.manager.get_font("alagard", 72),
                )
            )
        )

        self.text = self.master_container.add_child(
            Text(
                parent = self.master_container,
                text = "Lorem ipsum dolor sit amet\n, consectetur adipiscing elit.",
                style = Style(
                    alignment = "top-center",
                    offset = (0, self.title.rect.bottom + 16),
                    font = self.manager.get_font("alagard", 32),
                    fore_colour = (255, 255, 255),
                )
            )
        )
    def render_multiline_text(self, text: str, font: pygame.font.Font, colour: Colour) -> pygame.Surface:
        line_images = []
        for line in text.split("\n"):
            s = font.render(line, False, colour)
            line_images.append(s)

        width = max(line_images, key = lambda s: s.get_width())
        height = sum(line_images, key = lambda s: s.get_height())
        image = pygame.Surface((width, height), pygame.SRCALPHA)

        ty = 0
        for l in line_images:
            r = l.get_rect(centerx = width / 2, y = ty)
            image.blit(l, r)
            ty += r.height

        return image

    def on_key_down(self, key: int, unicode: str) -> None:
        super().on_key_down(key, unicode)
        if key == pygame.K_ESCAPE:
            self.parent.set_screen("menu")

    def on_resize(self, new_res: Vec2) -> None:
        super().on_resize(new_res)
        self.master_container.style.size = new_res
        self.master_container.style.image = util.draw_background(new_res)
        self.master_container.on_resize(new_res)

    def render(self, window: pygame.Surface) -> None:
        self.master_container.render(window)