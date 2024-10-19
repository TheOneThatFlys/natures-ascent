from __future__ import annotations

import pygame, inspect, pickle, os

from typing import Any, Callable
from dataclasses import is_dataclass

from engine import Node, Logger, Screen
from engine.ui import *
from engine.types import *

from .parsers import SaveHelper
from .constants import *

INDEX_SPECIAL_STRING = "$$"
ALLOWED_REC_TYPES = (DebugExpandable, list, dict, set, tuple, pygame.Rect, pygame.FRect, pygame.Vector2, pygame.sprite.Group)
SAVE_PATH = os.path.join("debug", "config.dat")

def render_rich_text(font: pygame.font.Font, text: str) -> pygame.Surface:
    """
    Renders a section of rich text.

    Formatting:
    - %(colour) to set colour - defaults to (0, 0, 0).

    e.g. `"%(255, 0, 0)this is red. %(255, 255, 255)this is white."`
    """

    text_sections = []

    current_colour = (0, 0, 0)
    current_section = ""
    index = 0
    # loop through input string
    while index < len(text):
        letter = text[index]
        # add character to current section if not escaping
        if letter != "%":
            current_section += letter
            index += 1
        # if valid escape is used followed by an opening bracket
        elif text[index + 1] == "(":
            # if the previous text section is not empty,
            # render the previous section of text and
            # start a new section
            if current_section != "":
                text_sections.append(font.render(current_section, True, current_colour))
                current_section = ""

            # grab the entire colour escape clause
            # e.g. (255, 0, 0)
            inside_loop_idx = index
            inside_acc = ""
            while inside_loop_idx < len(text):
                inside_loop_idx += 1
                inside_acc += text[inside_loop_idx]
                if text[inside_loop_idx] == ")":
                    break
            else:
                raise ValueError(f"Rich text render of '{text}' failed: missing closing bracket.")

            # create a colour tuple from the string
            current_colour = tuple(map(int, inside_acc.removeprefix("(").removesuffix(")").replace(" ", "").split(",")))
            
            # offset the main loop pointer by the length of the escape clause
            index = inside_loop_idx + 1
        # %% escape
        elif text[index + 1] == "%":
            current_section += "%"
            index += 2
        # invalid escape clause
        else:
            raise ValueError(f"Rich text render of '{text}' failed: % with no opening bracket.")

    # add the last section if it was not already escaped
    if current_section != "":
        text_sections.append(font.render(current_section, True, current_colour))
        current_section = ""

    # create a surface of the max bounds of the text added together
    surf = pygame.Surface((
        sum(s.get_width() for s in text_sections),
        max((s.get_height() for s in text_sections), default = 0),
    ), pygame.SRCALPHA)

    # render each section of text side by side
    x_offset = 0
    for section in text_sections:
        surf.blit(section, (x_offset, 0))
        x_offset += section.get_width()

    return surf

class Path:
    def __init__(self, values: tuple = ()) -> None:
        self.__v = values

    def add(self, value) -> Path:
        return Path(self.__v + (value,))

    def get_dirs(self) -> list:
        return self.__v

    def get_parent_path(self) -> Path:
        return Path(self.__v[:-1])
    
    def get(self) -> tuple:
        return self.__v
    
    def get_str(self, seperator: str = "."):
        return seperator.join(map(str, self.__v))

    def __str__(self) -> str:
        return self.get_str(".")
    
    def __hash__(self) -> int:
        return str(self).__hash__()
    
    def __eq__(self, value: Path) -> bool:
        return str(self) == str(value)

class CheckBox(Button):
    def __init__(self, parent: Element, style: Style, value: bool = False, enabled: bool = True, on_toggle: Callable[..., None] = None) -> None:
        super().__init__(parent, style, enabled = enabled, on_click = self.__toggle_v, hover_sound = None, click_sound = None, hover_style = None)

        self.value = value
        self.on_toggle = on_toggle

        self.redraw_image()

    def __toggle_v(self) -> None:
        self.value = not self.value
        if self.on_toggle: self.on_toggle()

    def redraw_image(self) -> None:
        self.tick_surface = pygame.Surface(self.style.size - pygame.Vector2(4, 4))
        self.tick_surface.fill(self.style.fore_colour)

        self.image = pygame.Surface(self.style.size)
        self.image.fill(self.style.colour)
        pygame.draw.rect(self.image, self.style.fore_colour, (0, 0, *self.style.size), width = 1)
        self.rect = self.image.get_rect()
        self.calculate_position()

    def render(self, window: pygame.Surface) -> None:
        super().render(window)

        if self.enabled and self.value:
            window.blit(self.tick_surface, self.tick_surface.get_rect(center = self.rect.center))

    def set_value(self, v: bool) -> None:
        self.value = v

    def update(self) -> None:
        return super().update()

class ImagePreview(Element):
    def __init__(self, parent: Element, style: Style, enabled: bool = True) -> None:
        super().__init__(parent, style)
        self.enabled = enabled

    def redraw_image(self) -> None:
        super().redraw_image()

        if self.style.visible:
            pygame.draw.rect(self.image, self.style.fore_colour, self.image.get_rect(), 1)

    def update(self) -> None:
        super().update()
        if self.enabled:
            self.redraw_image()

class Inspector(Element):
    def __init__(self, parent: AttributeEditor) -> None:
        super().__init__(parent, Style(
            size = (175, 0),
            alignment = "top-right",
            offset = (8, 8),
        ))

        self.parent: AttributeEditor

        self.background_colour = (33, 34, 44)
        norm_font = pygame.font.SysFont("Consolas", 12, bold = True)

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
            initial_text = "",
            enabled = False,
            on_unfocus = (self._on_value_unfocus, []),
            text_padding = (0, -2),
            style = Style(
                size = (self.rect.right - self.value_text_const.rect.right - 8, self.value_text_const.rect.height),
                offset = (self.value_text_const.rect.width + self.value_text_const.style.offset[0], self.value_text_const.style.offset[1] - 2),
                colour = parent.background_colour,
                font = norm_font,
                fore_colour = parent.text_colour,
                antialiasing = True,
                window = "debug"
            ),
            focused_style = Style(
                colour = parent.background_colour_2
            )
        ))

        self.value_check_box = self.add_child(CheckBox(
            self,
            enabled = False,
            value = False,
            on_toggle = self._on_value_toggle,
            style = Style(
                visible = False,
                size = (self.value_text_const.rect.height, self.value_text_const.rect.height),
                offset = self.value_text_box.style.offset,
                colour = self.background_colour,
                fore_colour = parent.text_colour,
                font = norm_font,
                antialiasing = True,
                window = "debug",
            )
        ))

        self.value_execute_box = self.add_child(Button(
            self,
            style = Style(
                image = norm_font.render("<call>", True, self.parent.text_colour),
                offset = self.value_text_box.style.offset + pygame.Vector2(0, 2),
                visible = False,
                window = "debug"
            ),
            on_click = self._on_value_click,
            enabled = False,
            hover_sound = None,
            click_sound = None,
        ))

        self.value_preview_box = self.add_child(ImagePreview(
            parent = self,
            style = Style(
                offset = self.value_text_const.style.offset + pygame.Vector2(0, self.value_text_const.rect.height + 2),
                stretch_type = "expand",
                size = (self.rect.width - 8, self.rect.width - 8),
                fore_colour = parent.background_colour_2,
                visible = False
            )
        ))

        self.style.size = (self.style.size[0], self.value_preview_box.rect.bottom - 4)

        self.possible_boxes = [self.value_text_box, self.value_check_box, self.value_execute_box, self.value_preview_box]

        self.attribute_path: Path | None = None

        self.redraw_image()

    def set_attribute_value(self, path: Path|str, value: Any) -> None:
        def __rec_set(path: Path|str, new_value: Any):
            if isinstance(path, Path):
                parent_path =  path.get_parent_path()
                pc = self.parent.get_item_from_path(parent_path)
                key = path.get()[-1]
            elif isinstance(path, str):
                parent_path = ".".join(path.split(".")[:-1])
                pc = self.parent.get_item_from_string(parent_path)
                key = path.split(".")[-1]

            if isinstance(pc, dict):
                pc[key] = new_value

            elif isinstance(pc, list):
                index = int(key.removeprefix(INDEX_SPECIAL_STRING))
                pc[index] = new_value

            elif isinstance(pc, tuple):
                index = int(key.removeprefix(INDEX_SPECIAL_STRING))
                new_tuple = pc[:index] + (new_value,) + pc[index + 1:]
                __rec_set(parent_path, new_tuple)

            elif isinstance(pc, (pygame.Rect, pygame.FRect)):
                if key == "x": pc.x = new_value
                elif key == "y": pc.y = new_value
                elif key == "width": pc.width = new_value
                elif key == "height": pc.height = new_value

            elif isinstance(pc, pygame.Vector2):
                if key == "x": pc.x = new_value
                elif key == "y": pc.y = new_value

            else:
                pc.__dict__[key] = new_value

        __rec_set(path, value)
        Logger.debug(f"Set {path} to {value}")

    def _on_value_unfocus(self) -> None:
        self.set_attribute_value(self.attribute_path, type(self.parent.get_item_from_path(self.attribute_path))(self.value_text_box.text))

    def _on_value_toggle(self) -> None:
        self.set_attribute_value(self.attribute_path, self.value_check_box.value)

    def _on_value_click(self) -> None:
        func = self.parent.get_item_from_path(self.attribute_path)
        res = func()
        Logger.debug(f"Method {self.attribute_path.get_str('.')}() returned {res}")

    def set_input_box(self, box: Element) -> None:
        for b in self.possible_boxes:
            if b == box:
                b.style.visible = True
                b.enabled = True
            else:
                b.style.visible = False
                b.enabled = False

    def set_attribute_info(self, path: Path) -> None:
        self.attribute_path = path
        if path == None:
            self.type_text_var.set_text("N/A")
            self.name_text_var.set_text("N/A")
            self.value_text_box.set_text("")

            self.set_input_box(self.value_text_box)
            self.value_text_box.enabled = False
        else:
            value = self.parent.get_item_from_path(path)
            self.type_text_var.set_text(str(type(value).__name__))
            name = path.get()[-1]
            if isinstance(name, str) and name.startswith(INDEX_SPECIAL_STRING):
                name = "index " + name.removeprefix(INDEX_SPECIAL_STRING)
            self.name_text_var.set_text(str(name))

            if type(value) == bool:
                self.set_input_box(self.value_check_box)
                self.value_check_box.set_value(value)

            elif type(value) == pygame.Surface:
                self.set_input_box(self.value_preview_box)
                self.value_preview_box.style.image = value
                self.value_preview_box.redraw_image()

            elif inspect.ismethod(value):
                self.set_input_box(self.value_execute_box)

            else:
                self.set_input_box(self.value_text_box)
                self.value_text_box.set_text(str(value))

    def update(self) -> None:
        super().update()
        self.image = pygame.Surface((self.style.size))
        self.image.fill(self.background_colour)

class Console(Element):
    def __init__(self, parent: AttributeEditor, height: int):
        self.parent: AttributeEditor
        super().__init__(
            parent,
            style = Style(
                size = (parent.style.size[0], height),
                alignment = "bottom-left",
                colour = (33, 34, 44),
                offset = (0, -height),
                font = parent.font,
                window = "debug",
                fore_colour = parent.text_colour
            )
        )

        self.text_history = self.add_child(ScrollableElement(
            parent = self,
            scroll_factor = 15.0,
            style = Style(
                size = (self.style.size[0], height - 24),
                alpha = 0,
                offset = (0, 4),
                alignment = "top-center",
                window = "debug",
            )
        ))

        self.text_enter = self.add_child(TextBox(
            parent = self,
            text_padding = (4, -2),
            on_unfocus = (self._on_enter, ()),
            style = Style(
                alignment = "bottom-left",
                antialiasing = True,
                offset = (8, 8),
                size = (self.style.size[0] - 16, 16),
                colour = parent.background_colour_2,
                font = parent.font,
                window = "debug",
                fore_colour = parent.text_colour,
            )
        ))

        self.n = 0
        self.line_height = 16

        self.col_norm = (255, 255, 255)
        self.col_dark = self.parent.text_colour_faint
        self.col_high = self.parent.str_colour
        self.col_num = self.parent.num_colour
        self.col_type = self.parent.type_colour
        self.col_error = (180, 20, 20)

    def parse_command(self, text: str) -> str:
        args = text.split(" ")
        if len(args) == 0: return "No command issued"
        cmd = args[0].lower()
        match cmd:
            case "ping":
                return f"%{self.col_highlight}Pong!"
            
            case "set":
                if len(args) != 3: return f"Unexpected number of arguments (expected %{self.col_num}2%{self.col_norm}, got %{self.col_num}{len(args) - 1}%{self.col_norm})"
                path_to_value = args[1]
                try:
                    current_type = type(self.parent.get_item_from_string(path_to_value))
                except ValueError:
                    return f"Invalid path: %{self.col_high}{path_to_value}%{self.col_norm}"
                try:
                    new_v = current_type(args[2])
                except ValueError:
                    return f"Invalid value for type %{self.col_type}{current_type.__name__}"
                self.parent.inspector.set_attribute_value(path_to_value, new_v)
                return ""
            
            case "call":
                if len(args) != 2: return f"Unexpected number of arguments (expected %{self.col_num}1%{self.col_norm}, got %{self.col_num}{len(args) - 1}%{self.col_norm})"
                path_to_value = args[1]
                try:
                    func = self.parent.get_item_from_string(path_to_value)
                except ValueError:
                    return f"Invalid path: %{self.col_high}{path_to_value}%{self.col_norm}"
                if not isinstance(func, Callable): return f"Error: %{self.col_high}{path_to_value} is not callable"
                res = func()
                return f"%{self.col_high}{path_to_value} returned {res}"
            
            case "chest":
                if self.manager.game.current_screen != "level": return f"Command only callable in %{self.col_high}'level'%{self.col_norm} screen"
                self.parse_command("call game.debug_palette.spawn_chest")
                return ""
        
            case _:
                return f"Unknown command: %{self.col_high}{cmd}"

    def _on_enter(self) -> None:
        if self.text_enter.text == "": return

        self.add_line(f"%{self.col_dark}> {self.text_enter.text}")
        response = self.parse_command(self.text_enter.text)
        self.add_line(response)

        self.text_enter.set_text("")
        self.text_enter.focus()

    def add_line(self, text: str) -> None:
        if text == "": return
        img = render_rich_text(self.style.font, f"%{self.style.fore_colour}" + text)
        self.text_history.add_child(Element(self.text_history, style = Style(
            image = img,
            size = (self.style.size[0], self.line_height),
            stretch_type = "none",
            offset = (8, self.n * self.line_height),
        )))
        self.n += 1
        self.text_history.on_resize(self.style.size)
        self.text_history.scroll_by(-self.line_height)

        if self.text_history._scroll_amount != self.text_history._scroll_min:
            self.text_history._scroll_amount = self.text_history._scroll_min
            self.text_history.on_resize(self.style.size)

    def on_resize(self, new_size: Vec2) -> None:
        self.style.size = new_size[0], self.style.size[1]
        self.text_enter.size = (self.style.size[0] - 16, 16)
        self.text_history.size = (self.style.size[0], self.text_history.style.size[1])
        super().on_resize(new_size)

class AttributeEditor(Element):
    def __init__(self, parent: DebugWindow):
        self.console_size = 200
        super().__init__(parent, Style(size = (parent.rect.width, parent.rect.height - self.console_size)))

        self.font = pygame.font.SysFont("Consolas", 12, bold = True)
        self.line_height = self.font.get_linesize()

        self.TEST_VALUE_WOW = 10

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
        self.func_colour = (80, 250, 123)

        self.expanded_folders: set[str] = set()
        self.add_folder_chain(Path(["game"]))

        save_data = SaveHelper.load_file(SAVE_PATH, format = "bytes")
        if save_data: self.expanded_folders = pickle.loads(save_data)

        self.folder_buttons: dict[str, pygame.Rect] = {}
        self.attribute_buttons: dict[str, pygame.Rect] = {}

        self.highlighted_rect: pygame.Rect | None = None

        self.scroll_offset = 0

        self.inspector = self.add_child(Inspector(self))
        self.console = self.add_child(Console(self, self.console_size))

    def add_folder_chain(self, path: Path) -> None:
        """Add the path to expanded folders, along with all parents."""
        acc = Path()
        for dir in path.get():
            acc = acc.add(dir)
            self.expanded_folders.add(acc)

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

    def __group_dict_items(self, dict_items: list[tuple], caller: Any) -> list[tuple]:
        def __ranking(x) -> int:
            if isinstance(x, ALLOWED_REC_TYPES) or is_dataclass(x):
                return 0
            elif inspect.ismethod(x):
                return 2
            return 1
        
        if isinstance(caller, list): cmp2 = lambda x: int(x.removeprefix(INDEX_SPECIAL_STRING))
        else: cmp2 = str

        return sorted(dict_items, key = lambda str_val: (__ranking(str_val[1]), cmp2(str_val[0])))

    def render_lists(self) -> dict:
        def __rec_render(d: dict, path: Path, depth: int, caller) -> None:
            for k, v in self.__group_dict_items(d.items(), caller):
                if k == "manager" and caller != self.manager.game: continue
                if k == "parent": continue
                # calculate folder path of this item
                path_to_item = path.add(k)

                omit_name = isinstance(k, str) and k.startswith(INDEX_SPECIAL_STRING)

                type_str = f"%{self.type_colour}{v.__class__.__name__}"
                key_str = f"%{self.str_colour}{k.__repr__()}" if isinstance(caller, dict) and isinstance(k, str) else k 
                name_str = f"%{self.text_colour}{'' if omit_name else key_str}"

                # if not a base value
                if isinstance(v, ALLOWED_REC_TYPES) or is_dataclass(v):
                    # render the folder line and get bounding rect
                    folder_text = f"{type_str} {name_str}"
                    if isinstance(v, (list, set, dict, tuple)):
                        folder_text += f" %{self.text_colour_faint}({len(v)})"
                    bounding_rect = self.render_folder(folder_text, str(path_to_item), depth)
                    if bounding_rect:
                        # add a folder button
                        self.folder_buttons[path_to_item] = bounding_rect

                    # if the folder is expanded, render children
                    if path_to_item in self.expanded_folders:
                        thing_to_render: dict[str, Any]
                        if isinstance(v, (list, set, tuple)):
                            # use $$ to tell renderer to omit name
                            thing_to_render = {f"{INDEX_SPECIAL_STRING}{str(index)}": value for index, value in enumerate(v)}
                        elif isinstance(v, dict):
                            thing_to_render = v
                        elif isinstance(v, (pygame.Rect, pygame.FRect)):
                            thing_to_render = {"x": v.x, "y": v.y, "width": v.width, "height": v.height}
                        elif isinstance(v, pygame.Vector2):
                            thing_to_render = {"x": v.x, "y": v.y}
                        elif isinstance(v, pygame.sprite.Group):
                            thing_to_render = {f"{INDEX_SPECIAL_STRING}{str(index)}": sprite for index, sprite in enumerate(v.sprites())}
                        else:
                            methods = {x[0]: x[1] for x in inspect.getmembers(v, predicate = lambda x: inspect.ismethod(x) and len(inspect.signature(x).parameters) == 0)}
                            thing_to_render = {**v.__dict__, **methods} # merges 2 dicts
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
                    line_text = f"{type_str} {name_str}{op_str}{value_str}"
                    if inspect.ismethod(v): line_text = f"{type_str} %{self.func_colour}{key_str}"
                    bounding_rect = self.render_line("  " + line_text, depth)

                    # add attribute editor button
                    if bounding_rect and (isinstance(v, (int, float, str, pygame.Surface)) or inspect.ismethod(v)):
                        self.attribute_buttons[path_to_item] = bounding_rect

        self.current_line = 0
        self.folder_buttons = {}
        self.attribute_buttons = {}
        __rec_render({"game": self.manager.game}, Path(), 0, self.manager.game)

    def get_item_from_path(self, path: Path) -> Any:
        return self.get_item_from_string(path.get_str())

    def get_item_from_string(self, path) -> Any:
        split_path = path.split(".")
        if len(split_path) == "" or split_path[0] != "game":
            print(split_path)
            raise ValueError("Invalid path")
        current_node = self.manager.game
        if len(split_path) == 1: return current_node
        try:
            for dir in path.split(".")[1:]:
                if isinstance(current_node, (list, tuple)):
                    index = int(dir.removeprefix(INDEX_SPECIAL_STRING))
                    current_node = current_node[index]

                elif isinstance(current_node, dict):
                    current_node = current_node[dir]

                elif isinstance(current_node, (pygame.Rect, pygame.FRect, pygame.Vector2)):
                    current_node = current_node.__getattribute__(dir)

                else:
                    if dir in current_node.__dict__:
                        current_node = current_node.__dict__[dir]
                    else:
                        a = [m[1] for m in inspect.getmembers(current_node) if m[0] == dir]
                        if len(a) == 0: raise ValueError("Invalid path")
                        current_node = a[0]
        except KeyError:
            raise ValueError("Invalid path")
        return current_node

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

        for path, rect in self.attribute_buttons.items():
            if rect.collidepoint(mouse_pos):
                self.inspector.set_attribute_info(path)
                break
        else:
            self.inspector.set_attribute_info(None)

    def on_scroll(self, dx: int, dy: int) -> None:
        if self.rect.collidepoint(self.manager.get_mouse_pos("debug")):
            multipliter = 60 if pygame.key.get_pressed()[pygame.K_LCTRL] else 20
            self.scroll_offset += dy * multipliter
            if self.scroll_offset > 0:
                self.scroll_offset = 0
        super().on_scroll(dx, dy)

    def on_resize(self, new_size: Vec2) -> None:
        self.style.size = new_size[0], new_size[1] - self.console_size
        self.image = pygame.Surface(new_size)
        for item in self.get_all_children():
            item.redraw_image()

    def update_buttons(self) -> None:
        mouse_pos = self.manager.get_mouse_pos("debug")
        if self.inspector.rect.collidepoint(mouse_pos):
            self.highlighted_rect = None
            return
        
        for _, rect in list(self.folder_buttons.items()) + list(self.attribute_buttons.items()):
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
        self.window = pygame.Window("Nature's Ascent - Debug", (640, STARTUP_SCREEN_SIZE[1]))
        self.window.set_icon(self.manager.get_image("menu/tree"))
        self.window.resizable = True

        self.render_surface = self.window.get_surface()
        self.dead = False

        game_window = self.manager.get_window("main")
        monitor_size = pygame.display.get_desktop_sizes()[0]

        # create virtual rects representing windows and monitor
        monitor_rect = pygame.Rect(0, 0, *monitor_size)
        debug_win_rect = pygame.Rect(*self.window.position, *self.window.size)
        main_win_rect = pygame.Rect(*game_window.position, *game_window.size)

        # normal layout - main centered, debug to the left
        main_win_rect.center = monitor_rect.center
        debug_win_rect.right = main_win_rect.left - 50

        # if debug doesn't fit, shift to the right
        if debug_win_rect.left < 0:
            debug_win_rect.left = 0

        # but if this makes windows overlay, move game window to the right
        if main_win_rect.left < debug_win_rect.right:
            main_win_rect.left = debug_win_rect.right

        # if main window is shifted too far to the right,
        # resize debug window to fit
        if main_win_rect.right > monitor_rect.right:
            main_win_rect.right = monitor_rect.right
            self.window.size = monitor_rect.right - main_win_rect.width, self.window.size[1]

        self.rect.size = self.window.size

        # move actual windows according to their rects
        game_window.position = main_win_rect.topleft
        self.window.position = debug_win_rect.topleft

        game_window.focus()

        self.attribute_editor = self.add_child(AttributeEditor(self))

        self.manager.game.__setattr__("debug_palette", DebugPalette(self.manager.game))

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
        SaveHelper.save_file(pickle.dumps(self.attribute_editor.expanded_folders), SAVE_PATH, False)
        self.dead = True
        self.window.destroy()

class DebugPalette(Node):
    """Holds helper functions for faster debugging."""
    def __init__(self, parent: Node) -> None:
        super().__init__(parent)
        self.game = self.manager.game

    def go_to_boss(self) -> None:
        player = self.manager.get_object("player")
        fm = self.manager.get_object("floor-manager")
        player.rect.center = [room.bounding_rect.center for (_, room) in fm.rooms.items() if "boss" in room.tags][0]

    def go_to_upgrade(self) -> None:
        player = self.manager.get_object("player")
        fm = self.manager.get_object("floor-manager")
        player.rect.center = [room.bounding_rect.center for (_, room) in fm.rooms.items() if "upgrade" in room.tags][0]

    def kill_player(self) -> None:
        self.manager.get_object("player").kill()

    def complete_everything(self) -> None:
        fm = self.manager.get_object("floor-manager")
        for room in fm.rooms.values():
            room.force_completion()

    def force_win(self) -> None:
        self.game.set_screen("overview", game_data = self.manager.get_object("level").get_overview_data())

    def spawn_chest(self) -> None:
        from world import ItemChest, Chest
        player = self.manager.get_object("player")
        level = self.manager.get_object("level")
        itempool = self.manager.get_object("itempool")
        if not itempool.is_empty():
            chest = level.add_child(ItemChest(level, player.rect.center, itempool.roll()))
            colliding = True
            while colliding:
                colliding = False
                for s in self.manager.groups["interact"]:
                    if s == chest or not isinstance(s, Chest): continue
                    if chest.rect.colliderect(s.rect):
                        chest.rect.y += TILE_SIZE
                        colliding = True
        else:
            Logger.warn("Item pool is empty, cannot spawn chest.")

    def spawn_heart(self) -> None:
        from item import Health
        player = self.manager.get_object("player")
        level = self.manager.get_object("level")
        level.add_child(Health(level, (player.rect.centerx, player.rect.bottom + 16)))

    def max_items(self) -> None:
        player = self.manager.get_object("player")
        inv = player.inventory
        if inv.primary: inv.primary.upgrade(3)
        if inv.spell: inv.spell.upgrade(3)