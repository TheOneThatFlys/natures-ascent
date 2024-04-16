# TODO:
# Settings: config loader
# Enemies spawn randomly in rooms
# Different rooms - shop etc
# Weapon system - equip & inv
# Weapon upgrades

from __future__ import annotations

import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

import pygame
pygame.init()
from typing import Type
from engine import Screen, Manager
from screens import Level, Menu, Settings
from util import Logger

from engine.types import *
from util.constants import *

class Game:
    # main game class that manages screens and pygame events
    def __init__(self) -> None:
        
        # set mode to keep image loader happy, then create an sdl window
        # pygame.display.set_mode((1, 1))
        self.window = pygame.Window("Nature's Ascent", SCREEN_SIZE)
        self.clock = pygame.time.Clock()

        self.running = True

        self.manager = Manager(self, fps = FPS, num_channels = 32)
        self.manager.set_pixel_scale(PIXEL_SCALE)
        self.load_assets()

        self.window.set_icon(self.manager.get_image("menu/tree"))

        # dictionary to hold screens
        self._screens: dict[str, Type[Screen]] = {}

        self.current_screen: str = None
        self.current_screen_instance: Screen

        self.add_screen("level", Level)
        self.add_screen("menu", Menu)
        self.add_screen("settings", Settings)
        self.set_screen("menu")

    @Logger.time(msg = "Loaded assets in %t seconds.")
    def load_assets(self):
        self.manager.load()

    def queue_close(self) -> None:
        "Quits program after current game loop finishes"
        self.running = False

    def add_screen(self, name: str, screen: Type[Screen]) -> None:
        "Add screen object to screen dictionary, key being screen.name"
        self._screens[name] = screen

    def set_screen(self, screen_name: str) -> None:
        "Sets the current screen based on screen name"
        if screen_name == self.current_screen: return
        self.current_screen = screen_name
        self.current_screen_instance = self._screens[screen_name](self)

    def set_windowed(self, new_size: Vec2) -> None:
        """Resizes the active window to the new resolution provided."""
        Logger.info(f"Set video mode to WINDOWED ({new_size[0]}, {new_size[1]})")
        self.window.size = new_size
        self.window.borderless = False
        self.window.set_windowed()

    def set_fullscreen(self, *, borderless: bool = False) -> None:
        """Sets the active window to fullscreen (or borderless fullscreen if specified)."""
        if borderless:
            self.window.borderless = True
            self.window.position = (0, 0)
            self.window.size = pygame.display.get_desktop_sizes()[0]
            Logger.info(f"Set video mode to BORDERLESS_WINDOW {self.window.size}")
        else:
            Logger.info("Set video mode to FULLSCREEN")
            self.window.set_fullscreen(True)
        self.current_screen_instance.on_resize(self.window.size)

    def run(self) -> None:
        # main loop
        while self.running:
            # maintain constant fps
            self.clock.tick(self.manager.fps)
            # calculate dt
            self.manager.update_dt()

            # poll events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.queue_close()

                # delegate certain events to current screen
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F9:
                        # debug hot reload
                        self.load_assets()
                        self.current_screen_instance = self._screens[self.current_screen](self)

                    elif event.key == pygame.K_F11:
                        # true fullscreen
                        self.set_fullscreen(borderless=True)

                    self.current_screen_instance.on_key_down(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.current_screen_instance.on_mouse_down(event.button)
                elif event.type == pygame.VIDEORESIZE:
                    self.current_screen_instance.on_resize(event.size)

            # reset cursor image
            self.manager.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

            # update screen instance
            self.current_screen_instance.update()

            # call os to change cursor
            self.manager.load_cursor()

            # clear the window
            self.window.get_surface().fill((0, 0, 0))
            # draw screen to window
            self.current_screen_instance.render(self.window.get_surface())
            self.window.flip()

        pygame.quit()

if __name__ == "__main__":
    # initialise logging
    Logger.allow_all()
    Logger.info("Starting game.")
    Game().run()
    Logger.info("Game closed successfully.")
