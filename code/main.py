# TODO:
# Rooms block player in
# Enemies spawn randomly in rooms
# Settings: config loader
# Different rooms - shop etc
# Weapon system - equip & inv
# Weapon upgrades

from __future__ import annotations

import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

import pygame, random
pygame.init()
from typing import Type
from engine import Screen, Manager, Logger
from screens import Level, Menu, Settings
from util import DebugWindow

from engine.types import *
from util.constants import *

class Game:
    # main game class that manages screens and pygame events
    def __init__(self) -> None:
        
        self.window = pygame.Window("Nature's Ascent", STARTUP_SCREEN_SIZE)
        self.display_surface: pygame.Surface = self.window.get_surface()
        self.clock = pygame.time.Clock()

        self.running = True

        self.manager = Manager(self, fps = FPS, num_channels = 32)
        self.manager.set_pixel_scale(PIXEL_SCALE)
        self.load_assets()

        self.window.set_icon(self.manager.get_image("menu/tree"))

        self.manager.add_window(self.window, "main")

        if IN_DEBUG:
            self.debug_window = DebugWindow(self)
            self.manager.add_window(self.debug_window.window, "debug")

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
        self.manager.cleanup()
        self.current_screen = screen_name
        self.current_screen_instance = self._screens[screen_name](self)

    def set_windowed(self, new_size: Vec2) -> None:
        """Resizes the active window to the new resolution provided."""
        self.window.size = new_size
        self.window.borderless = False
        self.window.set_windowed()
        # place window in the middle of the monitor
        desktop_size = pygame.display.get_desktop_sizes()[0]
        self.window.position = (desktop_size[0] / 2 - self.window.size[0] / 2, desktop_size[1] / 2 - self.window.size[1] / 2)

        self.current_screen_instance.on_resize(new_size)
        Logger.info(f"Set video mode to WINDOWED ({new_size[0]}, {new_size[1]})")

    def set_fullscreen(self, *, borderless: bool = False) -> None:
        """Sets the active window to fullscreen (or borderless fullscreen if specified)."""
        if borderless:
            self.window.borderless = True
            self.window.position = (0, 0)
            self.window.size = pygame.display.get_desktop_sizes()[0]
            Logger.info(f"Set video mode to BORDERLESS_WINDOW {self.window.size}")
        else:
            self.window.set_fullscreen(True)
            Logger.info("Set video mode to FULLSCREEN")

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
                if event.type == pygame.WINDOWCLOSE:
                    if event.window == self.window:
                        self.queue_close()
                    elif IN_DEBUG and event.window == self.manager.get_window("debug"):
                        self.debug_window.kill()

                if event.type == pygame.MOUSEMOTION:
                    self.manager.on_mouse_motion(event.pos, list(self.manager.windows.keys())[list(self.manager.windows.values()).index(event.window)])

                # delegate certain events to current screen
                elif event.type == pygame.KEYDOWN:
                    # debug hotkeys
                    if IN_DEBUG:
                        # hot reload
                        if event.key == pygame.K_F9:
                            self.load_assets()
                            self.current_screen_instance = self._screens[self.current_screen](self)
                        # screen changes
                        elif event.key == pygame.K_F10:
                            self.set_windowed(STARTUP_SCREEN_SIZE)
                        elif event.key == pygame.K_F11:
                            self.set_fullscreen(borderless = True)
                        elif event.key == pygame.K_F12:
                            self.set_fullscreen()

                    elif event.key == pygame.K_KP1:
                        self.set_windowed(STARTUP_SCREEN_SIZE)
                    elif event.key == pygame.K_KP2:
                        self.set_fullscreen()
                    elif event.key == pygame.K_KP3:
                        self.set_fullscreen(borderless = True)

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
            self.display_surface.fill((0, 0, 0))
            # draw screen to window
            self.current_screen_instance.render(self.display_surface)
            self.window.flip()

            if IN_DEBUG:
                self.debug_window.update()

        pygame.quit()

def main():
    # initialise logging
    Logger.allow_all()
    Logger.info("Starting game.")
    Game().run()
    Logger.info("Game closed successfully.")

if __name__ == "__main__":
    main()
