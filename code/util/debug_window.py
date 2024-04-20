from __future__ import annotations

import pygame

from typing import Any, Type

from engine import Node, Manager, Screen
from engine.ui import *
from engine.types import *

from .misc import render_rich_text

class AttributeInfo:
    SUPPORTED = (int, float, str)
    def __init__(self, name: str, type: Type, rect: pygame.Rect):
        self.name = name
        self.type = type
        self.rect = rect

class Inspector(Element):
    def __init__(self, parent: AttributeEditor):
        super().__init__(parent, Style(
            size = (150, 250),
            alignment = "top-right",
            offset = (8, 8),
        ))

        self.background_colour = (33, 34, 44)

        self.title = self.add_child(Text(
            self,
            text = "INSPECTOR",
            style = Style(
                alignment = "top-center",
                offset = (0, 4),
                antialiasing = True,
                font = pygame.font.SysFont("Consolas", 16, bold = True),
                fore_colour = parent.op_colour
            )
        ))

        norm_font = pygame.font.SysFont("Consolas", 12, bold = True)

        self.type_text_const = self.add_child(Text(
            self,
            text = "Type  ",
            style = Style(
                offset  = (4, self.title.style.offset[1] + self.title.rect.height),
                fore_colour = parent.type_colour,
                antialiasing = True,
                font = norm_font
            )
        ))

        self.name_text_const = self.add_child(Text(
            self,
            text = "Name  ",
            style = Style.from_style(self.type_text_const.style, offset = (4, self.type_text_const.style.offset[1] + self.type_text_const.rect.height))
        ))

        self.value_text_const = self.add_child(Text(
            self,
            text = "Value ",
            style = Style.from_style(self.type_text_const.style, offset = (4, self.name_text_const.style.offset[1] + self.name_text_const.rect.height))
        ))

        self.type_text_var = self.add_child(Text(
            self,
            text = "N/A",
            style = Style(
                offset = (self.type_text_const.style.offset[0] + self.type_text_const.rect.width, self.type_text_const.style.offset[1]),
                fore_colour = parent.text_colour,
                antialiasing = True,
                font = norm_font
            )
        ))

        self.name_text_var = self.add_child(Text(
            self,
            text = "N/A",
            style = Style(
                offset = (self.name_text_const.style.offset[0] + self.name_text_const.rect.width, self.name_text_const.style.offset[1]),
                fore_colour = parent.text_colour,
                antialiasing = True,
                font = norm_font
            )
        ))

        self.value_text_box = self.add_child(TextBox(
            self,
            initial_text = "test",
            style = Style(
                size = (self.rect.right - self.value_text_const.rect.right - 8, self.value_text_const.rect.height + 4),
                offset = (self.value_text_const.rect.width + self.value_text_const.style.offset[0], self.value_text_const.style.offset[1] - 2),
                colour = parent.background_colour,
                font = norm_font,
                fore_colour = parent.text_colour,
                antialiasing = True,
                window = "debug",
            ),
            focused_style = Style(
                colour = parent.background_colour_2
            )
        ))

        self.attribute_info: AttributeInfo | None = None

    def set_attribute_info(self, ai: AttributeInfo | None) -> None:
        self.attribute_info = ai
        if ai == None:
            self.type_text_var.set_text("N/A")
            self.name_text_var.set_text("N/A")
        else:
            self.type_text_var.set_text(str(ai.type.__name__))
            self.name_text_var.set_text(str(ai.name))

    def update(self) -> None:
        super().update()
        self.image = pygame.Surface((self.style.size))
        self.image.fill(self.background_colour)

class AttributeEditor(Element):
    ALLOWED_REC = (Node, Manager, Style, list, dict, set)
    def __init__(self, parent: DebugWindow):
        super().__init__(parent, Style(size = parent.window.size))

        self.font = pygame.font.SysFont("Consolas", 12, bold = True)
        self.line_height = self.font.get_linesize()

        self.tab_length = self.font.size("  ")[0]
        self.tab_line_offset = self.font.size(" |")[0] / 2
        self.padding_left = 4
        self.padding_top = 4

        self.background_colour = (40, 42, 54)
        self.background_colour_2 = (49, 51, 65)

        self.text_colour = (255, 255, 255)
        self.text_colour_2 = (62, 64, 74)
        self.text_colour_faint = (98, 114, 164)

        self.type_colour = (139, 233, 253)
        self.op_colour = (255, 121, 198)
        self.num_colour = (189, 147, 249)
        self.str_colour = (241, 250, 129)

        self.expanded_folders: set[str] = set()
        self.expanded_folders.add("/Game")
        self.folder_buttons: dict[str, pygame.Rect] = {}
        self.attribute_buttons: dict[str, AttributeInfo] = {}

        self.highlighted_rect: pygame.Rect | None = None

        self.scroll_offset = 0

        self.inspector = self.add_child(Inspector(self))

    def render_line(self, rich_text: str, tab_index: int) -> pygame.Rect:
        position = pygame.Vector2(
            self.padding_left,
            self.current_line * self.line_height + self.scroll_offset + self.padding_top
        )
        self.current_line += 1
        if position.y < -50 or position.y > self.style.size[1]:
            return None

        for i in range(tab_index):
            pygame.draw.line(self.image, self.text_colour_2, (i * self.tab_length + self.tab_line_offset, position.y), (i * self.tab_length + self.tab_line_offset, position.y + self.line_height))

        # draw text
        s = render_rich_text(self.font, rich_text)
        self.image.blit(s, position + pygame.Vector2(tab_index * self.tab_length, 2))
        return pygame.Rect(0, position.y, self.style.size[0], s.get_height())

    def render_folder(self, rich_text: str, folder_path: str, tab_index: int) -> pygame.Rect:
        icon = "▼" if folder_path in self.expanded_folders else "►"
        return self.render_line(f"%{self.text_colour}{icon} {rich_text}", tab_index)

    def __group_dict_items(self, dict_items: list[tuple]) -> list[tuple]:
        return sorted(dict_items, key = lambda str_val: (not isinstance(str_val[1], self.ALLOWED_REC), str_val[0]))

    def render_lists(self) -> dict:
        def __rec_render(d: dict, path: str, depth: int, caller) -> None:
            for k, v in self.__group_dict_items(d.items()):
                if isinstance(k, str) and k.startswith("_Sprite_"): continue
                # calculate folder path of this item
                path_to_item = f"{path}/{k}"

                omit_name = isinstance(k, str) and k.startswith("$$")

                type_str = f"%{self.type_colour}{v.__class__.__name__}"
                key_str = f"%{self.str_colour}{k.__repr__()}" if isinstance(caller, dict) and isinstance(k, str) else k 
                name_str = f"%{self.text_colour}{'' if omit_name else key_str}"

                # if not a base value
                if isinstance(v, self.ALLOWED_REC):
                    # render the folder line and get bounding rect
                    folder_text = f"{type_str} {name_str}"
                    if isinstance(v, (list, tuple, set, dict)):
                        folder_text += f" %{self.text_colour_faint}({len(v)})"
                    bounding_rect = self.render_folder(folder_text, path_to_item, depth)
                    if bounding_rect:
                        # add a folder button
                        self.folder_buttons[path_to_item] = bounding_rect

                    # if the folder is expanded, render children
                    if path_to_item in self.expanded_folders:
                        thing_to_render: dict[str, Any]
                        if isinstance(v, (list, set)):
                            # use $$ to tell renderer to omit name
                            thing_to_render = {f"$${str(index)}": value for index, value in enumerate(v)}
                        elif isinstance(v, dict):
                            thing_to_render = v
                        else:
                            thing_to_render = v.__dict__
                        # recurse!
                        __rec_render(thing_to_render, path_to_item, depth + 1, v)
                else:
                    v_type = v.__class__
                    v_colour = self.text_colour
                    if v_type == int or v_type == float or v_type == bool:
                        v_colour = self.num_colour
                    elif v_type == str:
                        v_colour = self.str_colour

                    value = v
                    if isinstance(v, str):
                        value = v.__repr__()

                    value_str = f"%{v_colour}{value}"
                    op_str = f"%{self.op_colour}{'' if omit_name else ' = '}"
                    bounding_rect = self.render_line(f"{type_str} {name_str}{op_str}{value_str}", depth)

                    # add attribute editor button
                    if bounding_rect and isinstance(v, AttributeInfo.SUPPORTED):
                        self.attribute_buttons[path_to_item] = AttributeInfo(str(k), v_type, bounding_rect)

        self.current_line = 0
        self.folder_buttons = {}
        self.attribute_buttons = {}
        __rec_render(self.manager.game.__dict__, "", 0, self.manager.game)

    def on_mouse_down(self, button: int) -> None:
        super().on_mouse_down(button)
        mouse_pos = self.manager.get_mouse_pos("debug")
        if self.inspector.rect.collidepoint(mouse_pos): return

        for path, rect in self.folder_buttons.items():
            if rect.collidepoint(mouse_pos):
                if path in self.expanded_folders:
                    self.expanded_folders.remove(path)
                else:
                    self.expanded_folders.add(path)

        for path, ai in self.attribute_buttons.items():
            if ai.rect.collidepoint(mouse_pos):
                self.inspector.set_attribute_info(ai)

    def on_scroll(self, dx: int, dy: int) -> None:
        self.scroll_offset += dy * 20
        if self.scroll_offset > 0:
            self.scroll_offset = 0

    def on_resize(self, new_size: Vec2) -> None:
        self.style.size = new_size
        self.image = pygame.Surface(new_size)
        for item in self.get_all_children():
            item.redraw_image()

    def update_buttons(self) -> None:
        mouse_pos = self.manager.get_mouse_pos("debug")
        if self.inspector.rect.collidepoint(mouse_pos):
            self.highlighted_rect = None
            return
        
        for _, rect in list(self.folder_buttons.items()) + [(None, x[1].rect) for x in self.attribute_buttons.items()]:
            if rect.collidepoint(mouse_pos):
                self.highlighted_rect = rect
                self.manager.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                break
        else:
            self.highlighted_rect = None

    def update(self) -> None:
        super().update()
        self.update_buttons()
        self.image.fill(self.background_colour)
        if self.highlighted_rect:
            pygame.draw.rect(self.image, self.background_colour_2, self.highlighted_rect)
        self.render_lists()

class DebugWindow(Screen):
    def __init__(self, parent: Node) -> None:
        super().__init__(parent)
        self.window = pygame.Window("Nature's Ascent - Debug", (640, 480))
        self.window.set_icon(self.manager.get_image("menu/tree"))
        self.window.resizable = True

        self.render_surface = self.window.get_surface()

        game_window = self.manager.get_window("main")
        # move this window to the left of main game
        self.window.position = (game_window.position[0] - self.window.size[0], game_window.position[1])
        # focus back to main game
        game_window.focus()

        self.attribute_editor = self.add_child(AttributeEditor(self))

    def on_scroll(self, dx: int, dy: int) -> None:
        self.attribute_editor.on_scroll(dx, dy)

    def on_key_down(self, key: int, unicode: str) -> None:
        self.attribute_editor.on_key_down(key, unicode)

    def on_resize(self, new_size: Vec2) -> None:
        self.attribute_editor.on_resize(new_size)

    def on_mouse_down(self, button: int) -> None:
        self.attribute_editor.on_mouse_down(button)

    def update(self) -> None:
        self.attribute_editor.update()

        self.render_surface.fill((0, 0, 0))
        self.attribute_editor.render(self.render_surface)
        self.window.flip()

    def kill(self) -> None:
        self.window.destroy()
