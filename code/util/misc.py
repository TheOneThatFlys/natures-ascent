import pygame, math, random
from typing import Optional, Literal, TypeVar
from engine.types import *

from .constants import *

def draw_background(screen_size: tuple[int, int], pixel_scale: int = 8, line_thickness: int = 7, offset: int = 0, border_radius: int = 0) -> pygame.Surface:
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

def get_closest_direction(vector: pygame.Vector2) -> Direction:
    """Returns the closest cardinal direction of a vector"""

    # return right if its a 0 vector
    if vector.magnitude() == 0: return "right"

    # get most influential component:
    # x is more important
    if abs(vector.x) > abs(vector.y):
        if vector.x > 0:
            return "right"
        else:
            return "left"
    
    # y is more important (or equal)
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

def create_outline(image: pygame.Surface, pixel_scale: int = 1, outline_colour: Colour = WHITE) -> pygame.Surface:
    """Creates an outline around the image using the image's alpha values. The resulting image is the image size + 2 * ``pixel_scale`` to account for extra space."""
    # scale image to pixel scale
    img = pygame.transform.scale_by(image, 1 / pixel_scale)

    # add padding around the image to be able to fit an outline
    padded_image = pygame.Surface((img.get_width() + 2, img.get_height() + 2), pygame.SRCALPHA)
    padded_image.blit(img, (1, 1))
    # convert the image to a array of alpha values
    pa = pygame.PixelArray(padded_image)
    alphas = [[0 for _ in range(len(pa[0]))] for _ in range(len(pa))]
    for y in range(len(pa)):
        for x in range(len(pa[0])):
            alphas[y][x] = min(image.unmap_rgb(pa[y][x])[3], 1)
    pa.close()

    # helper function to retrieve pixel alphas, defaulting to 0 if out of bounds
    get_value = lambda x, y: alphas[y][x] if 0 <= x < len(alphas[0]) and 0 <= y < len(alphas) else 0

    # fill pixel according to algorithm in ______________
    new = pygame.Surface(padded_image.get_size(), pygame.SRCALPHA)
    newa = pygame.PixelArray(new)
    for y in range(padded_image.get_height()):
        for x in range(padded_image.get_width()):
            nx, ny = x, y
            if get_value(nx, ny) == 0:
                if get_value(nx + 1, ny) == 1 or \
                    get_value(nx - 1, ny) == 1 or \
                    get_value(nx, ny + 1) == 1 or \
                    get_value(nx, ny - 1) == 1:

                    newa[ny][nx] = image.map_rgb(outline_colour)

    return pygame.transform.scale_by(new, pixel_scale)

AlignmentType = Literal["left", "center", "right"]
def render_multiline(font: pygame.font.Font, text: str, colour: Colour, max_width: int, antialias: bool = True, alignment: AlignmentType = "left") -> pygame.Surface:
    """Render text with linewrap, supports rich text"""
    lines = []
    words = text.split(" ")
    current_line = ""
    for word in words:
        line_length = font.size(current_line + " " + word)[0]
        if line_length > max_width:
            lines.append(current_line)
            current_line = word
        else:
            current_line += " " + word
    if current_line != "":
        lines.append(current_line)

    rendered_lines = [font.render(line, antialias, colour) for line in lines]

    surf = pygame.Surface((
        max(s.get_width() for s in rendered_lines),
        sum(s.get_height() for s in rendered_lines)
    ), pygame.SRCALPHA)

    line_height = max(s.get_height() for s in rendered_lines)
    for i, line in enumerate(rendered_lines):
        rect = line.get_rect(y = line_height * i)
        if alignment == "left":
            rect.x = 0
        elif alignment == "center":
            rect.centerx = surf.get_width() / 2
        elif alignment == "right":
            rect.right = surf.get_width()
        surf.blit(line, rect)

    return surf

T = TypeVar("T")
def choose_weighted(weighted_dict: dict[T, int]) -> T:
        if not weighted_dict: raise ValueError("Need to provide a non-empty weighted dictionary.")
        total_weight = sum(weighted_dict.values())
        n = random.randrange(total_weight)

        for k, v in weighted_dict.items():
            n -= v
            if n < 0:
                return k