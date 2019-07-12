#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  __init__.py
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

"""mazegame is a 2D platform game, structured like a module. Read the README file for more details.

The module relevant files are stored in the 'src' directory:
__init__.py -- this file, containing general useful classes and constants.
mzgblocks.py -- contains all classes defining the blocks, the fundamental elements of the game.
mzgrooms.py -- contains the classes defining a room and the whole maze, with the main loop for the game.
mzgmenu.py -- contains the PyWidget class and its children, to define GUI interface,
    and the TopLev class which defines the game menu and the main loop for the GUI.
"""


import os
from pygame import Rect
import pygame.locals as pyloc
import numpy as np

MAIN_DIR = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))

#frame per second, time per frame
FPS = 30
TPF = 1 / FPS

#custom pygame events
DEATHEVENT = pyloc.USEREVENT
ENTERDOOREVENT = pyloc.USEREVENT +1
TAKEKEYEVENT = pyloc.USEREVENT + 2
CHECKPEVENT = pyloc.USEREVENT + 3
ONCLICKEVENT = pyloc.USEREVENT + 4
ENTERINGEVENT = pyloc.USEREVENT + 5
EXITINGEVENT = pyloc.USEREVENT + 6

ISGAME = True


def checksign(x):
    """Check the sign of the argument, returning 0 (x == 0), 1 (x > 0) or -1 (x < 0)"""
    if x == 0:
        return 0
    elif x > 0:
        return 1
    else:
        return -1

def pairextractor(iterable):
    """Take an iterable and generate pairs of its element in order"""
    for i, el in enumerate(iterable):
        if i % 2 == 0:
            x = el
        else:
            y = el
            yield [x, y]
    

class PosManager:
    """Manage the screen coordinates and conversion from arbitrary unit to pixel

    screen_size -- return screen resolution
    postopix -- convert an absolute position
    sizetopix -- convert sizes: size is an (x, y) pair
        denoting x and y sizes of a rect
    recttopix -- convert a pygame.Rect instance
    """
    
    #unit is pixel
    SIZE_X = 1000
    SIZE_Y = 1000

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
    def postopix(*pp):
        """Converts an absolute position from arbitrary units to pixel units"""
        xx, yy = PosManager._argspar(pp)
        px = round((xx / 1000) * PosManager.SIZE_X)
        py = round((yy / 1000) * PosManager.SIZE_Y)
        return [px, py]

    @staticmethod
    def pixtopos(xoff, yoff, *pp):
        """Converts pixels to absolute position in arbitrary units."""
        # ~ xx, yy = PosManager._argspar(pp)
        # ~ uxx = round(1000 * (xx - PosManager.MARGIN_X) / (PosManager.SIZE_X - 2*PosManager.MARGIN_X))
        # ~ uyy = round(1000 * (yy - PosManager.MARGIN_Y) / (PosManager.SIZE_Y - 2*PosManager.MARGIN_Y))
        # ~ return [uxx + (xoff*1000), uyy + (yoff*1000)]
        raise NotImplementedError("pixtopos")
        
    @staticmethod
    def sizetopix(*pp):
        """Converts size from arbitrary units to pixel units

        Size is an (x, y) pair denoting x and y sizes of a rect
        """
        xx, yy = PosManager._argspar(pp)
        px = round((xx / 1000) * PosManager.SIZE_X)
        py = round((yy / 1000) * PosManager.SIZE_Y)
        return [px, py]

    @staticmethod
    def recttopix(rr):
        """Converts a pygame.Rect or FlRect instance from arbitrary units to pixel units"""
        pos = PosManager.postopix(rr.x, rr.y)
        sz = PosManager.sizetopix(rr.width, rr.height)
        return Rect(pos[0], pos[1], sz[0], sz[1])


class FlRect:
    """Similar to pygame.Rect but uses float numbers.

    The class stores internally only coordinates, width and height.
    Other attributes are rendered through properties, with getter and setter:
    x, y: coordinates of the top-left corner of the rectangle.
    top, bottom: y coordinates of the top and bottom edges respectively.
    left, right: x coordinates of the left and right edges respectively.
    centerx, centery: coordinates of the centre of the rectangle.
    width, height: self-explanatory. 
    """
    
    def __init__(self, x, y, w, h):
        """Initialization:
        
        x, y - coordinates of top-left corner of the rectangle
        w, h - width and height
        """
        self._x = x
        self._y = y
        self._w = w
        self._h = h

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value
    
    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value
    
    @property
    def width(self):
        return self._w

    @width.setter
    def width(self, value):
        self._w = value

    @property
    def height(self):
        return self._h

    @height.setter
    def height(self, value):
        self._h = value

    @property
    def top(self):
        return self._y

    @top.setter
    def top(self, value):
        self._y = value

    @property
    def bottom(self):
        return self._y + self._h

    @bottom.setter
    def bottom(self, value):
        self._y = value - self._h

    @property
    def left(self):
        return self._x

    @left.setter
    def left(self, value):
        self._x = value

    @property
    def right(self):
        return self._x + self._w

    @right.setter
    def right(self, value):
        self._x = value - self._w

    @property
    def centerx(self):
        return self._x + (self._w / 2)

    @centerx.setter
    def centerx(self, value):
        self._x = value - (self._w / 2)

    @property
    def centery(self):
        return self._y + (self._h / 2)

    @centery.setter
    def centery(self, value):
        self._h = value - (self._h / 2)

    def __repr__(self):
        """String representation of the class"""
        return f"<FlRect({self._x}, {self._y}, {self._w}, {self._h})>"

    def get_rect(self, off=np.array([0, 0])):
        """Return a pygame.Rect object with rounded coordinates

        off is the screen offset (a 2-length array), to place the rect in the screen.
        default, no offset.
        """
        coff = off * 1000
        return Rect(round(self._x) - coff[0], round(self._y) - coff[1], round(self._w), round(self._h))

    def move(self, *off):
        """Equivalent to the 'move' method of pygame.Rect"""
        if isinstance(off[0], (tuple, list, np.ndarray)):
            xx = off[0][0]
            yy = off[0][1]
        else:
            xx = off[0]
            yy = off[1]
        return FlRect(self._x + xx, self._y + yy, self._w, self._h)

    def colliderect(self, other):
        """Equivalent to the 'colliderect' method of pygame.Rect"""
        boolx = (self.right - other.left) * (other.right - self.left) > 0
        booly = (self.bottom - other.top) * (other.bottom - self.top) > 0
        return boolx and booly

    def contains(self, other):
        """Equivalent to the 'contains' method of pygame.Rect"""
        boolx = (self.right >= other.right) and (self.left <= other.left)
        booly = (self.bottom >= other.bottom) and (self.top <= other.top)
        return boolx and booly

    def clip(self, other):
        """Equivalent to the 'clip' method of pygame.Rect. In case of no intersection, returns None"""
        if self.colliderect(other):
            cx = max(self.x, other.x)
            cy = max(self.y, other.y)
            cw = min(self.right, other.right) - cx
            ch = min(self.bottom, other.bottom) - cy
            return FlRect(cx, cy, cw, ch)
        else:
            return None

    def distance(self, other):
        """Calculate distance from another FlRect, using the center as reference.

        returns a 2-length numpy array holding the x and y component of the distance.
        """
        apos = np.array([self.centerx, self.centery])
        bpos = np.array([other.centerx, other.centery])
        return apos - bpos

