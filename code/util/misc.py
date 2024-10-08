import pygame, math, random
from typing import Optional, Literal, TypeVar
from engine.types import *

from .constants import *

def draw_background(screen_size: Vec2, pixel_scale: int = 8, line_thickness: int = 7, offset: int = 0, border_radius: int = 0) -> pygame.Surface:
    """Draw a striped background of given sized and scale onto surface"""
    bg = pygame.Surface((screen_size[0] / pixel_scale, screen_size[1] / pixel_scale), pygame.SRCALPHA)
    bg.fill(BG_NAVY)
    pygame.draw.rect(bg, BG_DARKNAVY, [0, 0, *bg.get_size()], width = line_thickness // 2)

    n_lines = int((max(screen_size[0], screen_size[1]) + min(screen_size[0], screen_size[1])) / pixel_scale / line_thickness)
    for x in range(n_lines):
        if x % 2 == 0:
            d = x * line_thickness + line_thickness / 2 + offset
            e = line_thickness
            pygame.draw.line(bg, BG_DARKNAVY, (d + e, -e), (-e, d + e), line_thickness)

    if border_radius > 0:
        mask = pygame.Surface(bg.get_size())
        pygame.draw.rect(mask, WHITE, [0, 0, *mask.get_size()], border_radius = border_radius)
        mask.set_colorkey(BLACK)
        mask = pygame.mask.from_surface(mask)
        bg = mask.to_surface(setsurface = bg, unsetcolor = None)

    return pygame.transform.scale(bg, screen_size)

def draw_background_empty(size: Vec2):
    """Draw unstriped background."""
    image = pygame.Surface(size)
    image.fill(BG_NAVY)
    pygame.draw.rect(image, BG_DARKNAVY, (0, 0, *size), 24)
    return image

def create_gui_image(size: Vec2, pixel_scale: int = 2, rounded: bool = True, border_colour: Colour = UI_BROWN, bg_colour: Colour = UI_ALTBROWN, highlight_colour: Colour = UI_ALTLIGHTBROWN, shadow_colour: Colour = UI_ALTDARKBROWN) -> pygame.Surface:
    r = 2 if rounded else 0
    d = r / 2
    image = pygame.Surface(pygame.Vector2(size) / pixel_scale, pygame.SRCALPHA)
    pygame.draw.rect(image, border_colour, (0, 0, *image.get_size()), width = 1, border_radius = r)
    pygame.draw.rect(image, bg_colour, (1, 1, image.get_width() - 2, image.get_height() - 2))
    pygame.draw.line(image, highlight_colour, (1, 1), (image.get_width() - 2, 1))
    pygame.draw.line(image, shadow_colour, (d, image.get_height() - 1), (image.get_width() - 1 - d, image.get_height() - 1))
    return pygame.transform.scale_by(image, pixel_scale)

def get_closest_direction(vector: pygame.Vector2) -> Direction:
    """Returns the closest cardinal direction of a vector"""

    # return right if its a 0 vector
    if vector.magnitude() == 0: return "right"

    # get most influential component, priority of x:
    if abs(vector.x) > abs(vector.y):
        if vector.x > 0:
            return "right"
        else:
            return "left"
    
    # y priority (or equal)
    else:
        if vector.y > 0:
            return "down"
        else:
            return "up"
        
def get_direction_vector(direction: Direction) -> tuple[int, int]:
    """Get a normalised vector in the direction specified e.g. get_direction_vector("left") returns (-1, 0)"""
    match direction:
        case "left":
            return (-1, 0)
        case "right":
            return (1, 0)
        case "up":
            return (0, -1)
        case "down":
            return (0, 1)
        
def get_direction_angle(direction: Direction) -> int:
    """Get the angle in degrees of a direction"""
    match direction:
        case "left":
            return 180
        case "right":
            return 0
        case "up":
            return 90
        case "down":
            return -90
        
def polar_to_cart(angle_degrees: float, magnitude: float) -> pygame.Vector2:
    angle_radians = math.radians(angle_degrees)
    return pygame.Vector2(
        math.cos(angle_radians) * magnitude,
        -math.sin(angle_radians) * magnitude,
    )

def sign(n: float) -> Literal[1, -1, 0]:
    """Returns 1 if n is positive, -1 if negative, and 0 if 0"""
    if n > 0: return 1
    if n < 0: return -1
    return 0

def create_outline(image: pygame.Surface, pixel_scale: int = 1, outline_colour: Colour = (255, 255, 255)) -> pygame.Surface:
    """Creates an outline around the image using the image's alpha values. The resulting image is the image size + 2 * `pixel_scale` to account for extra space."""
    # scale image to pixel scale
    img = pygame.transform.scale_by(image, 1 / pixel_scale)

    # add padding around the image to be able to fit an outline
    padded_image = pygame.Surface((img.get_width() + 2, img.get_height() + 2), pygame.SRCALPHA)
    padded_image.blit(img, (1, 1))
    # convert the image to a array of alpha values
    pa = pygame.PixelArray(padded_image)
    pa_width, pa_height, *_ = pa.shape
    alphas = [[0 for _ in range(pa_width)] for _ in range(pa_height)]
    for x in range(pa_width):
        for y in range(pa_height):
            alphas[y][x] = 1 if image.unmap_rgb(pa[x, y])[3] > 0 else 0
    pa.close()

    # helper function to retrieve pixel alphas, defaulting to 0 if out of bounds
    get_value = lambda x, y: alphas[y][x] if 0 <= x < len(alphas[0]) and 0 <= y < len(alphas) else 0

    # fill pixel if adjacent pixel is opaque
    new = pygame.Surface((pa_width, pa_height), pygame.SRCALPHA)
    newa = pygame.PixelArray(new)
    for x in range(pa_width):
        for y in range(pa_height):
            if get_value(x, y) == 0:
                if (get_value(x + 1, y) == 1 or
                    get_value(x - 1, y) == 1 or
                    get_value(x, y + 1) == 1 or
                    get_value(x, y - 1) == 1):

                    newa[x, y] = image.map_rgb(outline_colour)

    return pygame.transform.scale_by(new, pixel_scale)

T = TypeVar("T")
def choose_weighted(weighted_dict: dict[T, int]) -> T:
        if not weighted_dict: raise ValueError("Need to provide a non-empty weighted dictionary.")
        total_weight = sum(weighted_dict.values())
        n = random.randrange(total_weight)

        for k, v in weighted_dict.items():
            n -= v
            if n < 0:
                return k
            
def lerp_colour(c1: Colour, c2: Colour, t: float) -> Colour:
    return (
        c1[0] + (c2[0] - c1[0]) * t,
        c1[1] + (c2[1] - c1[1]) * t,
        c1[2] + (c2[2] - c1[2]) * t,
    )

def is_valid_username(name: str) -> bool:
    """
    Check if the input string is a valid username. Valid usernames have a max of 16 chars and only contain alphanumeric characters and underscore.
    """
    if len(name) > 16: return False
    if name == "": return False

    for letter in name:
        if letter not in ALLOWED_CHARACTERS: return False

    return True

def seconds_to_stime(total_seconds: float) -> str:
    """Convert seconds to a string formatted time"""
    total_minutes = total_seconds // 60
    total_hours = total_minutes // 60
    int_hours = int(total_hours)
    int_minutes = int(total_minutes) % 60
    int_seconds = int(total_seconds) % 60
    int_ms = int(total_seconds % 1 * 100)
    if int_hours > 0:
        st = f"{int_hours}h {int_minutes}m {int_seconds}s"
    elif int_minutes > 0:
        st = f"{int_minutes}m {int_seconds}s {int_ms}ms"
    else:
        st = f"{int_seconds}s {int_ms}ms"
    return st