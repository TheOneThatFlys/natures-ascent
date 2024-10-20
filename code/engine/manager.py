from __future__ import annotations
from typing import TYPE_CHECKING, Literal

import pygame, os
from .logger import Logger
from .types import DebugExpandable

if TYPE_CHECKING:
    from .node import Node
    from ..main import Game

class Font():
    def __init__(self, font_path: str) -> None:
        self._fonts = {}
        self.path = font_path

    def get(self, font_size: int) -> pygame.font.Font:
        # if font already cached, then return cached font
        if font_size in self._fonts:
            return self._fonts[font_size]
        
        # else create a new font and add to the cache
        new_font = pygame.font.Font(self.path, font_size)
        self._fonts[font_size] = new_font
        return new_font

class Manager(DebugExpandable):
    def __init__(self, game: Game, fps: int = 60, num_channels = 8) -> None:
        self.game = game

        # stores groups
        self.groups: dict[str, pygame.sprite.Group] = {}

        # stores objects of interest
        self.objects: dict = {}

        # stores windows
        self.windows: dict[str, pygame.Window] = {}
        self.focused_window: str = "main"

        # stores mouse positions of windows
        self._window_mouse_positions: dict[str, tuple[int, int]] = {}

        # stores loaded assets
        self.assets: dict = {"image": {}, "sound": {}, "font": {}}
        
        # store volume percentages (0-1 inclusive)
        self._sfx_volume = 0.1
        self._music_volume = 0.1

        # store current music to prevent multiple playback
        self._current_music: str = ""

        # store keybinds
        self.keybinds: dict[str, int] = {}

        self.fps: int = fps
        self._dt_adjusted: float = 1
        self._dt_raw: float = 1 / fps

        self._load_scale: int = 1

        self._current_cursor: int = pygame.SYSTEM_CURSOR_ARROW

        pygame.mixer.set_num_channels(num_channels)

    @property
    def dt(self) -> float:
        return self._dt_adjusted
    
    @property
    def dt_raw(self) -> float:
        return self._dt_raw
    
    @property
    def sfx_volume(self) -> float:
        return self._sfx_volume
    
    @sfx_volume.setter
    def sfx_volume(self, v) -> None:
        self._sfx_volume = v

    @property
    def music_volume(self) -> float:
        return self._music_volume
    
    @music_volume.setter
    def music_volume(self, v) -> None:
        self._music_volume = v
        pygame.mixer.music.set_volume(v * 3)

    def update_dt(self) -> None:
        """Updates delta time for current frame. Should be called every frame"""

        # do not change these hardcoded values
        self._dt_raw = self.game.clock.get_time() / 1000
        self._dt_raw = min(self._dt_raw, 0.05) # limit to 3 frame skips
        self._dt_adjusted = 60 * self._dt_raw

    def add_object(self, id: str, node: Node) -> Node:
        self.objects[id] = node
        return node
    
    def add_window(self, window: pygame.Window, id: str) -> pygame.Window:
        self.windows[id] = window
        self._window_mouse_positions[id] = (-1, -1)
        return window

    def get_window(self, id: str) -> pygame.Window:
        return self.windows[id]
    
    def remove_object(self, id: str) -> None:
        del self.objects[id]

    def get_object(self, id: str) -> Node|None:
        return self.objects.get(id, None)

    def add_groups(self, names: list[str]) -> None:
        for name in names:
            self.groups[name] = pygame.sprite.Group()

    def get_mouse_pos(self, window_id: str = "main") -> tuple[int, int]:
        """Get mouse position in the given window"""
        return self._window_mouse_positions[window_id]
    
    def on_mouse_motion(self, position: tuple[int, int], window_id: str) -> None:
        self._window_mouse_positions[window_id] = position

    def cleanup(self) -> None:
        """Call this when switching scenes to avoid memory buildup."""
        self.groups = {}
        self.objects = {}

    def set_pixel_scale(self, scale: int) -> None:
        """Set scale for loading assets"""
        self._load_scale = scale

    def set_cursor(self, cursor_enum: int) -> None:
        self._current_cursor = cursor_enum

    def load_cursor(self) -> None:
        pygame.mouse.set_cursor(self._current_cursor)

    def load(self) -> None:
        """
        Loads all supported files in ./assets

        Assets folder must contain image, font, sound sub directories

        Supported files:
        - png
        - ttf
        - mp3
        """

        # clear assets in case this function was called multiple times
        self.assets = {"image": {}, "sound": {}, "font": {}}

        # maps folder name to extension
        ext_dir_map = {
            "png": "image",
            "ttf": "font",
            "mp3": "sound",
        }

        for dirpath, dirnames, filenames in os.walk("assets"):
            # go through each file
            for filename in filenames:

                fullpath = os.path.join(dirpath, filename)
                extension = os.path.splitext(filename)[1][1:]
                loaded_asset = None

                if extension == "png":
                    try:
                        loaded_asset = pygame.image.load(fullpath).convert_alpha()
                    except pygame.error as e:
                        Logger.error(f"Could not load image file at {fullpath}.", e)
                        loaded_asset = pygame.image.load(os.path.join(dirpath, "image", "error.png"))

                    # scale asset up
                    loaded_asset = pygame.transform.scale(
                        loaded_asset,
                        (
                            loaded_asset.get_width() * self._load_scale,
                            loaded_asset.get_height() * self._load_scale
                        )
                    )
                
                elif extension == "ttf":
                    loaded_asset = Font(fullpath)

                elif extension == "mp3" and "music" not in fullpath: # don't load music files as they will be streamed
                    loaded_asset = pygame.mixer.Sound(fullpath)

                if loaded_asset:
                    # trim path down
                    key = fullpath.removeprefix(os.path.join("assets", ext_dir_map[extension]) + os.sep).removesuffix(os.extsep + extension)
                    # replace backslashes with forward
                    key = key.replace(os.sep, "/")
                    self.assets[ext_dir_map[extension]][key] = loaded_asset

    def get_path_from_key(self, key: str, type: Literal["image", "font", "sound"]) -> str:
        type_ext_map = {
            "image": "png",
            "font": "ttf",
            "sound": "mp3",
        }

        return os.path.join("assets", type, *key.split("/")) + os.extsep + type_ext_map[type]

    def get_image(self, name: str, scale: float = 1.0) -> pygame.Surface:
        try:
            return pygame.transform.scale_by(self.assets["image"][name], scale)
        except KeyError:
            Logger.warn(f"Failed to fetch image at key {name}")
            return self.assets["image"]["error"]
    
    def get_font(self, name: str, size: int) -> pygame.font.Font:
        try:
            return self.assets["font"][name].get(size)
        except KeyError:
            Logger.warn(f"Failed to fetch font at key {name}")
            return pygame.font.Font(None, size)
    
    def get_sound(self, name: str) -> pygame.mixer.Sound:
        return self.assets["sound"][name]
    
    def play_music(self, key: str, volume: float = 1.0, fade_ms: int = 0) -> None:
        if self._current_music != key:    
            pygame.mixer.music.load(self.get_path_from_key(key, "sound"))
            pygame.mixer.music.set_volume(volume * self.music_volume * 3)
            pygame.mixer.music.play(-1, fade_ms=fade_ms)
            self._current_music = key

    def stop_music(self, fade_ms: int = 0) -> None:
        pygame.mixer.music.fadeout(fade_ms)
        self._current_music = ""

    def play_sound(self, sound_name: str, volume: float = 1.0, loop = False, fade_ms: int = 0) -> None:
        s = self.get_sound(sound_name)
        volume_multiplier = 10 * self._sfx_volume
        s.set_volume(volume * volume_multiplier)
        n_loops = -1 if loop else 0
        s.play(n_loops, fade_ms = fade_ms)
