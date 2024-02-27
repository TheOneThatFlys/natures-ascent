from __future__ import annotations
import pygame
from dataclasses import dataclass, replace, fields
from .types import *

IGNORED_MERGE_PROPERTIES = ("size", "offset")

@dataclass
class Style:
    visible: bool = True
    size: tuple[int, int] = (0, 0)

    position: Position = "relative"
    alignment: Alignment = "top-left"
    offset: tuple[int, int] = (0, 0)

    border_thickness = 0

    colour: Colour = (0, 0, 0)
    fore_colour: Colour = (0, 0, 0)
    border_colour: Colour = (0, 0, 0)

    font: pygame.font.Font = None

    image: pygame.Surface = None
    stretch_type: StretchType = "none"

    @staticmethod
    def from_style(style: Style, **changes) -> Style:
        "Returns a shallow copy of style with changes."
        return replace(style, **changes)
    
    @staticmethod
    def merge(style1: Style, style2: Style) -> Style:
        """
        Returns a new style with merged properties from style1 and style2; properties from style2 will take priority.\n
        Ignored properties:
        - size
        - offset
        """

        # if one of the styles is None, return the other
        if style1 == None: return Style.from_style(style2)
        if style2 == None: return Style.from_style(style1)

        new_style = Style()

        # loop through each field in dataclass
        for field in fields(Style):

            style1_val = getattr(style1, field.name)
            style2_val = getattr(style2, field.name)
            default_val = getattr(new_style, field.name)

            # if there are no conflicts, merge - straightfoward
            if style1_val == style2_val:
                setattr(new_style, field.name, style1_val)

            # if there are conflicts...
            else:
                # style 1 value is assigned if style 2 value is default (omitted)
                if style2_val == default_val:
                    setattr(new_style, field.name, style1_val)
                else:
                    # style 2 value is assigned if style 2 is specified
                    setattr(new_style, field.name, style2_val)

        return new_style