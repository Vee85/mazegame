#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  mzgscreen.py
#  
#  Copyright 2019 Valentino Esposito <valentinoe85@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

"""Contains classes to manage the screen division.

"""

import os
import math
import numpy as np
import pygame
from pygame import sprite
import pygame.locals as pyloc

import src


class ScreenArea(sprite.Sprite, src.PosManager):
    """Define an area of the screen.

    Child of Sprite and PosManager.
    This class holds a FlRect object to define an area of the screen. Provide useful methods
    for coordinate transformations to ensure that blocks coordinates are referred to the ScreenArea
    and not the whole screen.
    Useful to define different rectangular sections of the screen (game area, info bars, and similar).
    """

    def __init__(self, x, y, w, h, xm, ym):
        """Initializator: unit is arbitrary, from 0 to 1000. Refers to the whole screen.

        - x and y are coordinates of the top-left corner
        - w, h are width and height of the rectangle
        - xm and ym are x and y margings, added to the 1000 unit base. They allow to show
        the closest parts of the next offset 
        """
        super(ScreenArea, self).__init__()
        if x + w > 1000:
            raise ValueError("Error in defining ScreenArea position, x + w > 1000 is out of screen.")
        if y + h > 1000:
            raise ValueError("Error in defining ScreenArea position, y + h > 1000 is out of screen.")
        self.aurect = src.FlRect(x, y, w, h)
        self.image = pygame.Surface((w, h))
        self._xmargin = xm
        self._ymargin = ym

    def origin_area(self, off):
        """Returns the FlRect of the original area mapping the ScreenArea"""
        coff = off * 1000
        return src.FlRect(coff[0]-self._xmargin, coff[1]-self._ymargin, 1000+(2*self._xmargin), 1000+(2*self._ymargin))

    def postopix(self, xoff, yoff, *pp):
        """Converts an absolute position from arbitrary units to pixel units"""
        xx, yy = src.PosManager._argspar(pp)
        xx = xx - (xoff * 1000)
        yy = yy - (yoff * 1000)
        ax = (xx / 1000) * (self.aurect.width -2*self._xmargin) + self._xmargin
        ay = (yy / 1000) * (self.aurect.height - 2*self._ymargin) + self._ymargin
        return src.PosManager.postopix(ax, ay)
    
    def sizetopix(self, *pp):
        """Converts size from arbitrary units to pixel units"""
        xx, yy = src.PosManager._argspar(pp)
        ax = (xx / 1000) * (self.aurect.width -2*self._xmargin)
        ay = (yy / 1000) * (self.aurect.height -2*self._ymargin)
        return src.PosManager.sizetopix(ax, ay)

    def recttopix(self, rr, xoff, yoff):
        """Converts a pygame.Rect or FlRect instance from arbitrary units to pixel units"""
        pos = self.postopix(xoff, yoff, rr.x, rr.y)
        sz = self.sizetopix(rr.width, rr.height)
        return pygame.Rect(pos[0], pos[1], sz[0], sz[1])

    def pixtopos(xoff, yoff, *pp):
        """Converts pixel coordinate to absolute position in arbitrary units."""
        # ~ xx, yy = src.PosManager._argspar(pp)
        # ~ uxx = round(1000 * (xx - PosManager.MARGIN_X) / (PosManager.SIZE_X - 2*PosManager.MARGIN_X))
        # ~ uyy = round(1000 * (yy - PosManager.MARGIN_Y) / (PosManager.SIZE_Y - 2*PosManager.MARGIN_Y))
        # ~ return [uxx + (xoff*1000), uyy + (yoff*1000)]
        raise NotImplementedError("pixtopos")

    def corrpix(self, pos):
        """Return corrected pixel position"""
        if isinstance(pos, (src.FlRect, pygame.Rect)):
            return pos.move(self.aurect.x, self.aurect.y)
        elif isinstance(pos, (list, tuple, np.ndarray)):
            return (pos[0] + self.aurect.x, pos[1] + self.aurect.y)


#area where the maze is shown for gaming
mazearea = ScreenArea(0, 0, 800, 800, 20, 20)

#area where the maze is shown for editing
editorarea = ScreenArea(0, 0, 1000, 1000, 20, 20)
