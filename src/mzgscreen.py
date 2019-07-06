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


class ScreenArea:
    """Define an area of the screen.
    
    This class holds a FlRect object to define an area of the screen. Provide useful methods
    for coordinate transformations to ensure that blocks coordinates are referred to the ScreenArea
    and not the whole screen.
    Useful to define different rectangular sections of the screen (game area, info bars, and similar).
    """

    def __init__(self, x, y, w, h):    
        """Initializator: unit is arbitrary, from 0 to 1000. Refers to the whole screen.

        x and y are coordinates of the top-left corner
        w, h are width and height of the rectangle
        """
        if x + w > 1000:
            raise ValueError("Error in defining ScreenArea position, x + w > 1000 is out of screen.")
        if y + h > 1000:
            raise ValueError("Error in defining ScreenArea position, y + h > 1000 is out of screen.")
        self.area = src.FlRect(x, y, w, h)

    #@@@ fix below
    @staticmethod
    def screen_size():
        """Returns screen resolution"""
        return PosManager.SIZE_X, PosManager.SIZE_Y

    @staticmethod
    def _argspar(pp):
        """Parse the argument for other function, allowing variadics of two elements"""
        if isinstance(pp[0], (tuple, list, np.ndarray)):
            xx = pp[0][0]
            yy = pp[0][1]
        else:
            xx = pp[0]
            yy = pp[1]
        return float(xx), float(yy)

    @staticmethod
    def postopix(xoff, yoff, *pp):
        """Converts an absolute position from arbitrary units to pixel units"""
        xx, yy = PosManager._argspar(pp)
        xx = xx - (xoff * 1000)
        yy = yy - (yoff * 1000)
        px = round(((xx / 1000) * (PosManager.SIZE_X - 2*PosManager.MARGIN_X)) + PosManager.MARGIN_X)
        py = round(((yy / 1000) * (PosManager.SIZE_Y - 2*PosManager.MARGIN_Y)) + PosManager.MARGIN_Y)
        return [px, py]

    @staticmethod
    def pixtopos(xoff, yoff, *pp):
        """Converts pixels to absolute position in arbitrary units."""
        xx, yy = PosManager._argspar(pp)
        uxx = round(1000 * (xx - PosManager.MARGIN_X) / (PosManager.SIZE_X - 2*PosManager.MARGIN_X))
        uyy = round(1000 * (yy - PosManager.MARGIN_Y) / (PosManager.SIZE_Y - 2*PosManager.MARGIN_Y))
        return [uxx + (xoff*1000), uyy + (yoff*1000)]
    
    @staticmethod
    def sizetopix(*pp):
        """Converts size from arbitrary units to pixel units

        Size is an (x, y) pair denoting x and y sizes of a rect
        """
        xx, yy = PosManager._argspar(pp)
        px = round((xx / 1000) * (PosManager.SIZE_X - 2*PosManager.MARGIN_X))
        py = round((yy / 1000) * (PosManager.SIZE_Y - 2*PosManager.MARGIN_Y))
        return [px, py]

    @staticmethod
    def recttopix(xoff, yoff, rr):
        """Converts a pygame.Rect or FlRect instance from arbitrary units to pixel units"""
        pos = PosManager.postopix(xoff, yoff, rr.x, rr.y)
        sz = PosManager.sizetopix(rr.width, rr.height)
        return Rect(pos[0], pos[1], sz[0], sz[1])
