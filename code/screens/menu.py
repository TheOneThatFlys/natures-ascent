import pygame
from typing import Callable, Iterable
from engine import Screen
from engine.ui import Element, Style, Text, Button
from util import parse_spritesheet

class TextButtonMenu(Button):
    def __init__(self, parent: Element, yoffset: int, text: str, on_click: Callable, click_args: Iterable = [], text_hover: str = None):
        super().__init__(
            parent = parent,
            style = Style(
                alignment = "top-center",
                offset = (0, yoffset),
                size = (1, 1),
                alpha = 0
            ),
            hover_style=None,
            on_click = self._on_click_with_sound,
            click_args = click_args
            )

        self.click_func = on_click

        text_size = self.manager.get_font("alagard", 32).size(text)
        self.style.size = text_size[0] + 4, text_size[1] + 4
        self.hover_style.size = self.style.size
        self.redraw_image()

        self.text = self.add_child(Text(
            self,
            Style(
                font = self.manager.get_font("alagard", 32),
                colour = (23, 68, 41),
                fore_colour = (99, 169, 65),
                alignment = "center-center",
                position = "relative",
                text_shadow = True,
            ),
            text
        ))

        self.text_normal = text
        self.text_hover = text_hover if text_hover else text

    def _on_click_with_sound(self, *args):
        self.manager.play_sound(sound_name = "button_click", volume = 0.3)
        self.click_func(*args)

    def update(self):
        super().update()
        if self.hovering and not self.last_hovering:
            self.manager.play_sound(sound_name = "button_hover", volume = 0.1)
            self.text.style.colour = (51, 22, 31)
            self.text.style.fore_colour = (95, 41, 46)
            self.text.set_text(self.text_hover)
            self.text.redraw_image()
        elif not self.hovering and self.last_hovering:
            self.text.style.colour = (23, 68, 41)
            self.text.style.fore_colour = (99, 169, 65)
            self.text.set_text(self.text_normal)
            self.text.redraw_image()

class Menu(Screen):
    def __init__(self, parent):
        super().__init__("menu", parent)
        
        self.master_container = Element(
            parent = self,
            style = Style(
                size = self.rect.size,
                image = self.draw_background(self.rect.size),
                stretch_type = "skew",
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
                    text_shadow = True,
                    font = self.manager.get_font("alagard", 72),
                )
            )
        )


        self.play_button = self.master_container.add_child(TextButtonMenu(
            parent = self.master_container,
            yoffset = self.title.rect.bottom + 16,
            text = "New Run",
            on_click = self.parent.set_screen,
            click_args = ["level",]
        ))

        self.leaderboard_button = self.master_container.add_child(TextButtonMenu(
            parent = self.master_container,
            yoffset = self.play_button.rect.bottom,
            text = "Leaderboard",
            on_click = self.parent.set_screen,
            click_args = ["menu",]
        ))

        self.settings_button = self.master_container.add_child(TextButtonMenu(
            parent = self.master_container,
            yoffset = self.leaderboard_button.rect.bottom,
            text = "Settings",
            on_click = self.parent.set_screen,
            click_args = ["menu",]
        ))
        
        self.exit_button = self.master_container.add_child(TextButtonMenu(
            parent = self.master_container,
            yoffset = self.settings_button.rect.bottom,
            text = "Exit",
            text_hover = ":c",
            on_click = self.parent.queue_close
        ))

        self.manager.play_sound(sound_name = "music/menu", volume = 0.5, loop = True)

    def draw_background(self, screen_size: tuple[int, int], pixel_scale: int = 6, line_thickness: int = 7) -> pygame.Surface:
        COLOUR_ONE = (37, 44, 55)
        COLOUR_TWO = (26, 30, 36)

        bg = pygame.Surface((screen_size[0] / pixel_scale, screen_size[1] / pixel_scale))
        bg.fill(COLOUR_ONE)

        n_lines = int((max(screen_size[0], screen_size[1]) + min(screen_size[0], screen_size[1])) / pixel_scale / line_thickness)
        for x in range(n_lines):
            if x % 2 == 0:
                d = x * line_thickness + line_thickness / 2
                e = line_thickness
                pygame.draw.line(bg, COLOUR_TWO, (d + e, -e), (-e, d + e), line_thickness)

        width, height = bg.get_size()
        pygame.draw.line(bg, COLOUR_TWO, (0, 0), (width, 0), line_thickness)
        pygame.draw.line(bg, COLOUR_TWO, (0, 0), (0, height), line_thickness)
        pygame.draw.line(bg, COLOUR_TWO, (width - 1, 0), (width - 1, height), line_thickness)
        pygame.draw.line(bg, COLOUR_TWO, (0, height - 1), (width, height - 1), line_thickness)

        # pygame.draw.line(bg, COLOUR_TWO, (width - line_thickness / 2, height - line_thickness / 2), (width - line_thickness / 2, 0), line_thickness)

        return pygame.transform.scale(bg, screen_size)
            
    def on_resize(self, new_res):
        self.master_container.style.image = self.draw_background(new_res)

        self.master_container.style.size = new_res
        for item in self.master_container.get_all_children():
            item.redraw_image()

    def render(self, window):
        self.master_container.render(window)

    def update(self):
        self.master_container.update()

    def destroy(self):
        self.manager.get_sound("music/menu").stop()