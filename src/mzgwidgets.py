#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  mzgwidgets.py
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

"""Contains classes to build the game menu as a GUI in pygame itself and start the game.

PgWidget -- the base class for the widget. Provides basic event handler common to all widget.
All Widget are clickable.

PgLabel -- A label widget. Holds a text.

PgButton -- A button widget. Holds a text, which is highlighted when the mouse enters
in the surface area.

TopLev -- The class holding the menu, connecting the callbacks and starting the game.
"""

import sys
import os
from itertools import count
import numpy as np
import pygame
from pygame import sprite
import pygame.locals as pyloc

import src


class PgWidget(sprite.Sprite, src.PosManager):
    """Base class for all widgets do not use it directly, use its children.

    Keep tracks of all its instances, and provide common methods and event submitters
    using the pygame event system.
    enterevent -- emitted when the mouse enters the widget surface
    exitevent -- emitted when the mouse leaves the widget surface
    onclickevent -- emitted when a mouse button is clicked and the mouse is inside the widget surface
    connect -- method to connect a callback function to an event
    Most of its methods require a sscr argument: the pygame.display surface
    """
    
    _idcounter = count(0)
    allwidgets = sprite.Group()
    
    def __init__(self, surf, pos):
        """Initialization:
        
        surf -- a pygame.Surface, shown by the widget
        pos -- 2-length container, x y coordinates of the top-left corner of the surface 
        """
        super(PgWidget, self).__init__()
        self._id = next(self._idcounter)
        self.update = False
        if isinstance(surf, pygame.Surface):
            self.image = surf
        elif surf is None:
            self.image = pygame.Surface((10, 10))
        else:
            raise RuntimeError("Wrong initialization parameter.")
        self.pos = pos
        self.rect = self.image.get_rect().move(self.pos)
        self._shown = False
        self.allwidgets.add(self)
        self.connectedcalls = []

    @staticmethod
    def initcounter():
        """Reset the id generators of the widgets"""
        PgWidget._idcounter = count(0)

    @staticmethod
    def widget_list(shownonly=True):
        """Return a list all widget. If showonly is true, returns the widged displayed on the screen only"""
        if shownonly:
            return [ww for ww in PgWidget.allwidgets.sprites() if ww._shown]
        else:
            return PgWidget.allwidgets.sprites()

    def show(self, sscr, loadscreen=False):
        """Blit the widget.
        
        loadscreen -- boolean, useful for child classes who override this method
        """
        sscr.blit(self.image, self.pos)
        self._shown = True

    def wupdate(self, sscr):
        """Update the widget"""
        if self.update:
            self.show(sscr, False)
            self.update = False

    @staticmethod
    def hideall(sscr, bgc):
        """Hide a screen, filling it with the bgc color

        bgc -- 3-length tuple of list, a RGB color
        """
        #ssrc must be the screen surface
        sscr.fill(bgc)
        for ww in PgWidget.widget_list():
            ww._shown = False
    
    def enter_event(self):
        """Post the enter event to the pygame.event system"""
        newev = pygame.event.Event(src.ENTERINGEVENT, key_id=self._id)
        pygame.event.post(newev)

    def exit_event(self):
        """Post the exit event to the pygame.event system"""
        newev = pygame.event.Event(src.EXITINGEVENT, key_id=self._id)
        pygame.event.post(newev)

    def onclick_event(self):
        """Post the onclick event to the pygame.event system"""
        newev = pygame.event.Event(src.ONCLICKEVENT, key_id=self._id)
        pygame.event.post(newev)

    def connect(self, eventtype, callback):
        """Connect a callback to an event type

        eventtype -- numeric costant corresponding to an event
        callback -- a callable
        """
        conn = (eventtype, callback)
        self.connectedcalls.append(conn)

    @staticmethod
    def clear_widgets():
        PgWidget.allwidgets.empty()


class PgLabel(PgWidget):
    """A Label, holding some text

    Child of PgWidget. Creates a text surface.
    """

    TEXTCOL = (255, 255, 255)
    
    def __init__(self, labtext, pos, textheight, font=None, textcolor=TEXTCOL):
        """Initialization:
        
        labtext -- text of the label
        pos -- 2-length container, x y coordinates of the top-left corner of the to be created surface
        textheight -- height of the text in pixels
        font -- the used font (default none)
        textcolor -- 3-length tuple of list, a RGB color (default white)
        """
        self.text = labtext
        self.font = font
        mfont = pygame.font.Font(self.font, self.sizetopix(0, textheight)[1])
        surftext = mfont.render(self.text, True, textcolor)
        super(PgLabel, self).__init__(surftext, self.postopix(pos))


class PgButton(PgWidget):
    """A button, holding some text, is highlighted when the mouse enters in the surface

    Child of PgWidget. Creates a text surface.
    """
    
    BGCOL = (0, 0, 0)
    HOVERCOL = (100, 100, 100)
    TEXTCOL = (255, 255, 255)
    
    def __init__(self, buttext, pos, textheight, font=None):
        """Initialization:
        
        buttext -- text of the button
        pos -- 2-length container, x y coordinates of the top-left corner of the to be created surface
        textheight -- height of the text in pixels
        font -- the used font (default none)
        """
        self.text = buttext
        self.font = font
        self.textheight = textheight
        wgsurf = self.drawbutton(self.BGCOL)
        super(PgButton, self).__init__(wgsurf, self.postopix(pos))

    def drawbutton(self, bgc):
        """creates the pygame.Surface instance with the text of the button"""
        mfont = pygame.font.Font(self.font, self.sizetopix(0, self.textheight)[1])
        surftext = mfont.render(self.text, True, self.TEXTCOL)
        surfbutton = pygame.Surface([surftext.get_width(), surftext.get_height()])
        surfbutton.fill(bgc)
        surfbutton.blit(surftext, (0, 0))
        return surfbutton

    def switchbgcol(self, bgc):
        """switch toe color of the background of the surface (for highlight when the mouse enters)"""
        self.image = self.drawbutton(bgc)
        self.update = True

    def show(self, ssrc, loadscreen=True):
        """override base method, draw the widget"""
        if loadscreen:
            self.switchbgcol(self.BGCOL)
        super(PgButton, self).show(ssrc)


class PgTextArea(PgWidget):
    
    TEXTCOL = (255, 255, 255)
    
    def __init__(self, pos, textheight, itext="", font=None, textcolor=TEXTCOL):
        """Initialization:
        
        labtext -- text of the label
        pos -- 2-length container, x y coordinates of the top-left corner of the to be created surface
        textheight -- height of the text in pixels
        font -- the used font (default none)
        textcolor -- 3-length tuple of list, a RGB color (default white)
        """
        self.text = itext
        self.textcol = textcolor
        self.textheight = textheight
        self.font = font
        super(PgTextArea, self).__init__(None, self.postopix(pos))
        
    def write(self, txt):
        self.text = txt
        mfont = pygame.font.Font(self.font, self.sizetopix(0, self.textheight)[1])
        self.image = mfont.render(self.text, True, self.textcol)
