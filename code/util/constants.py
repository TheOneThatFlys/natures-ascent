import sys, os

STARTUP_SCREEN_SIZE = 1280, 720
FPS = 60

IN_DEBUG = "-debug" in sys.argv or "-d" in sys.argv

TILE_SIZE = 64
PIXEL_SCALE = 2

SURFACE_FRICTION_COEFFICIENT = 0.2

HEALTH_VISIBILITY_TIME = 60

ANIMATION_FRAME_TIME = 10

RUN_SAVE_PATH = os.path.join("saves", "current_run.dat")
CONFIG_SAVE_PATH = os.path.join("saves", "config.json")

INTERACT_DISTANCE = TILE_SIZE * 1.5