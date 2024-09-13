from __future__ import annotations

import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
working_directory = os.path.join(__file__, os.pardir, os.pardir) # set cwd as two parents from this file
os.chdir(working_directory)

import sys, platform, uuid, datetime, json
import pygame

from typing import Type
from engine import Screen, Manager, Logger, Node
from screens import Level, Menu, SettingsScreen, GameOverviewScreen
from util import DebugWindow, SaveHelper, AutoSaver

from engine.types import *
from util.constants import *

if IN_DEBUG:
    from world import Chest, ItemChest
    from item import Health

class DebugPalette(Node):
    """Holds helper functions for faster debugging."""
    def __init__(self, parent: Node) -> None:
        super().__init__(parent)
        self.game: Game = self.manager.game

    def go_to_boss(self) -> None:
        player = self.manager.get_object("player")
        fm = self.manager.get_object("floor-manager")
        player.rect.center = [room.bounding_rect.center for (_, room) in fm.rooms.items() if "boss" in room.tags][0]

    def kill_player(self) -> None:
        self.manager.get_object("player").kill()

    def force_win(self) -> None:
        self.game.set_screen("overview", game_data = self.manager.get_object("level").get_overview_data(), end_type = "win")

    def spawn_chest(self) -> None:
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
        player = self.manager.get_object("player")
        level = self.manager.get_object("level")
        level.add_child(Health(level, (player.rect.centerx, player.rect.bottom + 16)))

    def max_items(self) -> None:
        player = self.manager.get_object("player")
        inv = player.inventory
        if inv.primary: inv.primary.upgrade(3)
        if inv.spell: inv.spell.upgrade(3)

class Game(DebugExpandable):
    # main game class that manages screens and pygame events
    def __init__(self) -> None:
        pygame.init()
        
        self.window = pygame.Window("Nature's Ascent", STARTUP_SCREEN_SIZE)
        self.window.resizable = True
        self.display_surface: pygame.Surface = self.window.get_surface()
        self.clock = pygame.time.Clock()

        self._window_mode: WindowMode = "windowed"

        self.running = True

        self.manager = Manager(self, fps = FPS, num_channels = 32)
        self.manager.set_pixel_scale(PIXEL_SCALE)
        self.load_assets()

        self.window.set_icon(self.manager.get_image("menu/tree"))

        self.manager.add_window(self.window, "main")

        if IN_DEBUG:
            self.debug_window = DebugWindow(self)
            self.debug_palette = DebugPalette(self.debug_window)
            self.manager.add_window(self.debug_window.window, "debug")

        # dictionary to hold screens
        self._screens: dict[str, Type[Screen]] = {}

        self.current_screen: str = ""
        self.current_screen_instance: Screen

        # store screen changes to defer to next frame, to prevent key errors
        self._next_screen: str = ""
        self._next_screen_kwargs: dict = {}

        self.add_screen("level", Level)
        self.add_screen("menu", Menu)
        self.add_screen("settings", SettingsScreen)
        self.add_screen("overview", GameOverviewScreen)
        self.set_screen("menu")

        self.load_config()
        self.settings_saver = AutoSaver(self, CONFIG_SAVE_PATH, 60 * 120)

    @Logger.time(msg = "Loaded assets in %t seconds.")
    def load_assets(self):
        self.manager.load()

    def queue_close(self) -> None:
        """Quits program after current game loop finishes"""
        self.running = False

    def add_screen(self, name: str, screen: Type[Screen]) -> None:
        """Add screen object to screen dictionary, key being screen.name"""
        self._screens[name] = screen

    def set_screen(self, screen_name: str, **init_kwargs) -> None:
        """Sets the current screen based on screen name"""
        if screen_name == self.current_screen: return
        self._next_screen = screen_name
        self._next_screen_kwargs = init_kwargs

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
        self._window_mode = "windowed"

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
        self._window_mode = "borderless" if borderless else "fullscreen"
 
    def get_window_mode(self) -> WindowMode:
        return self._window_mode

    def get_config_as_string(self) -> str:
        config = {
            "window-mode": self.get_window_mode(),
            "sfx-vol": self.manager.sfx_volume,
            "music-vol": self.manager.music_volume,
            "keybinds": self.manager.keybinds
        }
        return json.dumps(config, indent=4)
    
    def load_config(self) -> None:
        default_config = {
            "window-mode": "windowed",
            "sfx-vol": 0.1,
            "music-vol": 0.1,
            "keybinds": {
                "move-up": pygame.K_w,
                "move-left": pygame.K_a,
                "move-down": pygame.K_s,
                "move-right": pygame.K_d,
                "attack-up": pygame.K_UP,
                "attack-left": pygame.K_LEFT,
                "attack-down": pygame.K_DOWN,
                "attack-right": pygame.K_RIGHT,
                "spell": pygame.K_SPACE,
                "interact": pygame.K_e,
                "pause": pygame.K_ESCAPE,
                "map-zoom-in": pygame.K_EQUALS,
                "map-zoom-out": pygame.K_MINUS,
            }
        }

        if not os.path.exists(CONFIG_SAVE_PATH):
            # load default values
            config = default_config
        else:
            config = json.loads(SaveHelper.load_file(CONFIG_SAVE_PATH))
           
        try:
            cfg_option = config["sfx-vol"]
            if not isinstance(cfg_option, (int, float)): raise TypeError(f"Incorrect type: {cfg_option}")
            if cfg_option < 0: raise ValueError(f"Value out of bounds: {cfg_option}")
            self.manager.sfx_volume = cfg_option
        except Exception as e:
            Logger.warn(f"Could not load config option [sfx-vol]. Defaulting to value {default_config['sfx-vol']} ({e})")

        try:
            cfg_option = config["music-vol"]
            if not isinstance(cfg_option, (int, float)): raise TypeError(TypeError(f"Incorrect type: ({cfg_option})"))
            if cfg_option < 0: raise ValueError(f"Value out of bounds: {cfg_option}")
            self.manager.music_volume = cfg_option
        except Exception as e:
            Logger.warn(f"Could not load config option [music-vol]. Defaulting to value {default_config['music-vol']} ({e})")

        try:
            window_mode: WindowMode = config["window-mode"]
            if window_mode != self._window_mode:
                match window_mode:
                    case "windowed":
                        self.set_windowed(STARTUP_SCREEN_SIZE)
                    case "fullscreen":
                        self.set_fullscreen()
                    case "borderless":
                        self.set_fullscreen(borderless = True)
                    case _:
                        raise ValueError(f"Unknown window mode: {window_mode}")
        except Exception as e:
            Logger.warn(f"Could not load config option [window-mode]. Defaulting to value {default_config['window-mode']} ({e})")

        try:
            cfg_option = config["keybinds"]
            for key in default_config["keybinds"].keys():
                if key not in cfg_option:
                    Logger.warn(f"Keybind to action {key} not found, loading default keybind instead.")
                    cfg_option[key] = default_config["keybinds"][key]
                if not isinstance(cfg_option[key], int):
                    Logger.warn(f"Keybind for action {key} is invalid type, loading default keybind instead.")   
                    cfg_option[key] = default_config["keybinds"][key]

            self.manager.keybinds = cfg_option
        except Exception as e:
            Logger.warn(f"Could not load config option [keybinds]. Loading default keybinds instead")
            self.manager.keybinds = default_config["keybinds"]

    def update_save(self) -> None:
        self.settings_saver.data = self.get_config_as_string()
        self.settings_saver.update()

    def run(self) -> None:
        # main loop
        while self.running:
            # maintain constant fps
            self.clock.tick(self.manager.fps)
            # calculate dt
            self.manager.update_dt()

            # change screen if needed
            if self._next_screen:
                self.manager.cleanup()
                self.current_screen = self._next_screen
                self.current_screen_instance = self._screens[self._next_screen](self, **self._next_screen_kwargs)
                self._next_screen = ""
                self._next_screen_kwargs = {}

            # poll events
            for event in pygame.event.get():
                screen_instance: Screen = self.current_screen_instance

                # send events to debug window if focused
                window = getattr(event, "window", None)
                if IN_DEBUG and window == self.manager.get_window("debug"):
                    screen_instance = self.debug_window

                if event.type == pygame.WINDOWCLOSE:
                    if IN_DEBUG:
                        self.debug_window.kill()
                    self.queue_close()

                if event.type == pygame.MOUSEMOTION:
                    # ------------------------------------- vvvvvv little hack to get key from a value in a dict
                    self.manager.on_mouse_motion(event.pos, list(self.manager.windows.keys())[list(self.manager.windows.values()).index(event.window)])

                # delegate certain events to current screen
                elif event.type == pygame.KEYDOWN:
                    # debug hotkeys
                    if IN_DEBUG:
                        # hot reload
                        if event.key == pygame.K_F9:
                            self.load_assets()
                            self.current_screen_instance = self._screens[self.current_screen](self)

                    screen_instance.on_key_down(event.key, event.unicode)

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    screen_instance.on_mouse_down(event.button)

                elif event.type == pygame.MOUSEBUTTONUP:
                    screen_instance.on_mouse_up(event.button)

                elif event.type == pygame.MOUSEWHEEL:
                    screen_instance.on_scroll(event.x, event.y)

                elif event.type == pygame.WINDOWRESIZED:
                    screen_instance.on_resize((event.x, event.y))

            # reset cursor image
            self.manager.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

            # update screen instance
            self.current_screen_instance.update()
            self.update_save()

            if IN_DEBUG and not self.debug_window.dead:
                self.debug_window.update()

            # call os to change cursor
            self.manager.load_cursor()

            # clear the window
            self.display_surface.fill((0, 0, 0))
            # draw screen to window
            self.current_screen_instance.render(self.display_surface)
            self.window.flip()

        self.settings_saver.force_save()
        pygame.quit()

def log_system_specs() -> None:
    """Logs system specs to standard logger"""
    uname = platform.uname()
    Logger.info(f"Found system specs [system] = {uname.system}")
    Logger.info(f"Found system specs [release] = {uname.release}")
    Logger.info(f"Found system specs [version] = {uname.version}")
    Logger.info(f"Found system specs [machine] = {uname.machine}")
    Logger.info(f"Found system specs [processor] = {uname.processor}")
    Logger.info(f"Found system specs [n-cores] = {os.cpu_count()}")

    Logger.info(f"Detected python version = {platform.python_version()}")
    Logger.info(f"Current working directory = {os.path.abspath(os.path.curdir)}")

def clean_debug_folder(max_logs: int) -> None:
    """Make sure only the {max_logs} newest logs are in debug folder."""
    folder_path = os.path.join("debug")
    # get all files ending with .log (and not profile)
    logs = list(map(
        lambda filename: os.path.join(folder_path, filename),
        filter(
            lambda filepath: filepath.endswith(".log") and not filepath == "profile.log",
            os.listdir(folder_path)
        )
    ))
    while len(logs) > max_logs:
        # get oldest file path
        oldest_file = min(logs, key = os.path.getctime)
        # remove file from system
        os.remove(oldest_file)
        # and also update log list
        logs.remove(oldest_file)

def main() -> None:
    # create a debug folder
    if not os.path.exists("debug"):
        os.mkdir("debug")

    # generate a unique session id
    session_id = uuid.uuid4()

    log_to_console = IN_DEBUG or "-cout" in sys.argv or "-c" in sys.argv
    # initialise logging
    Logger.start("$CONSOLE" if log_to_console else os.path.join("debug", f"{datetime.datetime.now():%H.%M.%S-%d.%m.%y}.log"))
    
    # keep newest 5 logs (5 total)
    clean_debug_folder(max_logs = 5)

    Logger.allow_all()
    Logger.info(f"Initialised session {session_id} on {datetime.datetime.now():%d/%m/%y %H:%M:%S}.")

    # get some system debug info
    if not log_to_console:
        log_system_specs()

    Logger.info("Starting game.")

    # profiling
    if "-profile" in sys.argv:
        from cProfile import run
        import pstats
        # create a debug folder
        if not os.path.exists("debug"):
            os.mkdir("debug")

        profile_path = os.path.join("debug", "profile.dat")
        log_path = os.path.join("debug", "profile.log")

        # run and profile the game
        run("Game().run()", profile_path, sort = "cumulative")

        # parse output dump and save to log
        with open(log_path, "w") as f:
            profile_stats = pstats.Stats(profile_path, stream = f)
            profile_stats.strip_dirs().sort_stats(pstats.SortKey.CUMULATIVE).print_stats()
        Logger.info(f"Saved performance profile to '{log_path}'.")
    else:
        # main entry point
        Game().run()

    Logger.info("Game closed successfully.")

if __name__ == "__main__":
    main()
