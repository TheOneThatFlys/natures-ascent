import pygame

from engine import Screen
from engine.ui import Element, Style, Text, Button
from engine.types import *
import util

from .common import TextButton, TextButtonColours

class Menu(Screen):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        
        self.master_container.style.alpha = 255
        self.master_container.style.image = util.draw_background(self.rect.size)
        self.master_container.redraw_image()

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
        ))

        self.manager.play_sound(sound_name = "music/menu", loop = True)

    def on_resize(self, new_res: Vec2) -> None:
        self.master_container.style.image = util.draw_background(new_res)
        super().on_resize(new_res)

class ScrollableText(Element):
    def __init__(self, parent: Element, style: Style, text: str, text_padding: int = 0, scroll_strength: int = 30) -> None:
        self.text = text
        self.text_padding = text_padding
        self.scroll_strength = scroll_strength

        self._scroll_progress = 0

        super().__init__(parent, style)

    def redraw_image(self) -> None:
        super().redraw_image()
        font_surf = self.style.font.render(self.text, self.style.antialiasing, self.style.fore_colour, wraplength = self.style.size[0] - 2 * self.text_padding)
        self.image.blit(font_surf, (self.text_padding, self.text_padding + self._scroll_progress))

    def on_scroll(self, dx: int, dy: int) -> None:
        super().on_scroll(dx, dy)

        if self.rect.collidepoint(self.manager.get_mouse_pos()):
            self._scroll_progress += dy * self.scroll_strength

            if self._scroll_progress > 0:
                self._scroll_progress = 0

            self.redraw_image()

class CreditsScreen(Screen):
    def __init__(self, parent) -> None:
        super().__init__(parent)

        self.master_container.style.alpha = 255
        self.master_container.style.image = util.draw_background(self.rect.size)
        self.master_container.redraw_image()

        self.title = self.master_container.add_child(
            Text(
                parent = self.master_container,
                text = "Legal Disclaimer",
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
            ScrollableText(
                parent = self.master_container,
                text = 
"""
By playing this game, you are submitting to the jurisdiction and internal governance of the developers. Any and all legal action will be met with equal and opposite opposition, and may, or may not, result in the incapacitation or permanant disfiguration of all parties involved.

The developers of this game are not liable for any damages that occur during the consumption of the game. This is including, but not limited to: heatstroke, headaches, back pain, rabies, acne, stroke, chest pain, miscarriage, shingles, osteoporosis, flooding, volcano eruption, avalanche, tsunami, ovarian cysts, unknown discharges of any colour, sudden death, wildfires, dizziness, loss of smell, constipation, false sense of wellbeing, eternal happiness.

This game created for entertainment purposes only. Any attempt to to use this product in an educational, promotional, or any other manner may result in unintended behaviour. This product is not to be used as protection from natural disasters, and repeated use may result in severe damage to the user's reproductive system. Reheating this product may result in the growth of unclassified bacteria and fungi; the developers take no responsibility for any and all resulting plagues or pandemics arisen from this.
""",
                style = Style(
                    alignment = "top-center",
                    offset = (0, self.title.rect.bottom + 16),
                    font = self.manager.get_font("alagard", 16),
                    size = (self.rect.width - 100, self.rect.height - 200),
                    colour = (0, 0, 0, 0),
                    fore_colour = (255, 255, 255),
                )
            )
        )

    def on_key_down(self, key: int, unicode: str) -> None:
        super().on_key_down(key, unicode)
        if key == pygame.K_ESCAPE:
            self.parent.set_screen("menu")

    def on_resize(self, new_res: Vec2) -> None:
        self.master_container.style.size = new_res
        self.master_container.style.image = util.draw_background(new_res)
        self.text.style.size = (self.rect.width - 100, self.rect.height - 200)

        super().on_resize(new_res)

    def render(self, window: pygame.Surface) -> None:
        self.master_container.render(window)