import pygame

def parse_spritesheet(spritesheet: pygame.Surface, *, frame_size: tuple[int, int] = None, frame_count: int = None, no_alpha: bool = False, flip: bool = False) -> list[pygame.Surface]:
    """
    Returns a list of surfaces containing each frame of the sprite sheet.

    Modifications to the base spritesheet will not affect the resulting frames.

    Only needs one of either frame_count or frame_size parameters.

    Spritesheet must contain each frame horizontally with no padding.
    """

    if frame_count != None:
        n = frame_count
        size = (spritesheet.get_width() / frame_count, spritesheet.get_height())
    elif frame_size != None:
        n = spritesheet.get_width() // frame_size[0]
        size = frame_size
    else:
        raise TypeError("Function parse_animation missing either parameter: frame_size or frame_count")

    frames = []
    for i in range(n):
        if no_alpha:
            frame = pygame.Surface(size)
        else:
            frame = pygame.Surface(size, pygame.SRCALPHA)
        frame.blit(spritesheet, (-i * size[0], 0))
        if flip:
            frame = pygame.transform.flip(frame, 1, 0)
        frames.append(frame)

    return frames