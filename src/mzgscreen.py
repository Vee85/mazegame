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


class ScreenArea(src.PosManager):
    """Define an area of the screen.

    Child of PosManager.
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
        if x + w > 1000:
            raise ValueError("Error in defining ScreenArea position, x + w > 1000 is out of screen.")
        if y + h > 1000:
            raise ValueError("Error in defining ScreenArea position, y + h > 1000 is out of screen.")
        self.area = src.FlRect(x, y, w, h)
        self._xmargin = xm
        self._ymargin = ym

    def origin_area(self, off):
        """Returns the FlRect of the original area mapping the ScreenArea"""
        coff = off * 1000
        return src.FlRect(coff[0]-self._xmargin, coff[1]-self._ymargin, coff[0]+1000+self._xmargin, coff[1]+1000+self._ymargin)

    def postopix(self, xoff, yoff, *pp):
        """Converts an absolute position from arbitrary units to pixel units"""
        xx, yy = src.PosManager._argspar(pp)
        xx = xx - (xoff * 1000)
        yy = yy - (yoff * 1000)
        ax = self.area.x + ((xx / 1000) * (self.area.width -2*self._xmargin) + self._xmargin)
        ay = self.area.y + ((yy / 1000) * (self.area.height - 2*self._ymargin) + self._ymargin)
        return src.PosManager.postopix(0, 0, ax, ay)
    
    def sizetopix(self, *pp):
        """Converts size from arbitrary units to pixel units"""
        xx, yy = src.PosManager._argspar(pp)
        ax = (xx / 1000) * (self.area.width -2*self._xmargin)  
        ay = (yy / 1000) * (self.area.height -2*self._ymargin)
        return src.PosManager.sizetopix(ax, ay)

    def recttopix(self, xoff, yoff, rr):
        """Converts a pygame.Rect or FlRect instance from arbitrary units to pixel units"""
        pos = self.postopix(xoff, yoff, rr.x, rr.y)
        sz = self.sizetopix(rr.width, rr.height)
        return pygame.Rect(pos[0], pos[1], sz[0], sz[1])
