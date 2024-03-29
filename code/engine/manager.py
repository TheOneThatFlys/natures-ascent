from __future__ import annotations
from typing import TYPE_CHECKING

import pygame, time, os

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

class Manager():
    def __init__(self, game: Game, fps: int = 60, num_channels = 8) -> None:
        self.game = game

        # stores groups
        self.groups: dict[str, pygame.sprite.Group] = {}
        # stores objects of interest
        self.objects: dict = {}
        # stores loaded assets
        self.assets: dict = {"image": {}, "sound": {}, "font": {}}
        # store current playing music
        self.music_current: str = ""

        self.fps: int = fps
        self._dt_constant: float = 60 / 1000 # makes dt values backwards compatible
        self.dt: float = 1

        self._load_scale: int = 1

        self._current_cursor: int = pygame.SYSTEM_CURSOR_ARROW

        pygame.mixer.set_num_channels(num_channels)

    def update_dt(self) -> None:
        "Updates delta time for current frame. Should be called every frame"
        self.dt = self._dt_constant * self.game.clock.get_time()

    def add_object(self, id: str, node: Node) -> Node:
        self.objects[id] = node
        return node
    
    def remove_object(self, id: str) -> None:
        del self.objects[id]

    def get_object_from_id(self, id: str) -> Node:
        return self.objects.get(id, None)

    def add_groups(self, names: list[str]) -> None:
        for name in names:
            self.groups[name] = pygame.sprite.Group()

    def cleanup(self) -> None:
        "Call this when switching scenes to avoid memory buildup."
        self.groups = {}
        self.objects = {}

    def set_pixel_scale(self, scale: int) -> None:
        "Set scale for loading assets"
        self._load_scale = scale

    def set_cursor(self, cursor_enum) -> None:
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
                    loaded_asset = pygame.image.load(fullpath).convert_alpha()
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

                elif extension == "mp3":
                    loaded_asset = pygame.mixer.Sound(fullpath)

                if loaded_asset:
                    # trim path down
                    key = fullpath.removeprefix(os.path.join("assets", ext_dir_map[extension]) + "\\").removesuffix("." + extension)
                    # replace backslashes with forward
                    key = key.replace("\\", "/")
                    self.assets[ext_dir_map[extension]][key] = loaded_asset

    def get_image(self, name: str) -> pygame.Surface:
        try:
            return self.assets["image"][name]
        except KeyError:
            return self.assets["image"]["error"]
    
    def get_font(self, name: str, size: int) -> pygame.font.Font:
        return self.assets["font"][name].get(size)
    
    def get_sound(self, name: str) -> pygame.mixer.Sound:
        return self.assets["sound"][name]
    
    def stop_music(self) -> None:
        # return if no music is playing
        if self.music_current == "": return
        
        self.get_sound(self.music_current).stop()
        self.music_current = ""

    def play_sound(self, sound_name: str, volume: float = 1.0, loop = False) -> None:
        if sound_name.startswith("music/"):
            # if trying to play the same track twice, just continue current
            if self.music_current == sound_name:
                return
            
            # stop previously playing music
            if self.music_current != "":
                self.get_sound(self.music_current).stop()

            self.music_current = sound_name

        s = self.get_sound(sound_name)
        s.set_volume(volume)
        n_loops = -1 if loop else 0
        s.play(n_loops)
