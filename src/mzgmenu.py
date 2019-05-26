#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  mzgmenu.py
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
from src.mzgrooms import Maze

GAME_DIR = os.path.join(src.MAIN_DIR, '../gamemaps')


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
            self.pos = pos
            self.rect = self.image.get_rect().move(self.pos)
            self._shown = False
            self.allwidgets.add(self)
            self.connectedcalls = []
        else:
            raise RuntimeError("Wrong initialization parameter.")

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
        super(PgLabel, self).__init__(surftext, self.postopix(0, 0, pos))


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
        super(PgButton, self).__init__(wgsurf, self.postopix(0, 0, pos))

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


class TopLev:
    """the game container. Represent the top level class, contaning the menu and the game.

    menuloop method is the main loop, other methods of this class are called inside the main loop.
    """
    
    BGCOL = (0, 0, 0)
    
    def __init__(self, screen):
        """Initialization:

        screen -- the pygame.display surface
        """
        self.fn = None
        self.mlstop = False
        self.screen = screen

        self.title = PgLabel("MAZEGAME", (300, 0), 100)        

        self.newbutt = PgButton("New Game", (100, 150), 50)
        self.newbutt.connect(src.ONCLICKEVENT, self.menunewgame)
        self.newbutt.connect(src.ENTERINGEVENT, lambda : self.newbutt.switchbgcol(PgButton.HOVERCOL))
        self.newbutt.connect(src.EXITINGEVENT, lambda : self.newbutt.switchbgcol(PgButton.BGCOL))

        self.loadbutt = PgButton("Load Game", (600, 150), 50)
        self.loadbutt.connect(src.ONCLICKEVENT, lambda : print(self.loadbutt.text))
        self.loadbutt.connect(src.ENTERINGEVENT, lambda : self.loadbutt.switchbgcol(PgButton.HOVERCOL))
        self.loadbutt.connect(src.EXITINGEVENT, lambda : self.loadbutt.switchbgcol(PgButton.BGCOL))

        self.quitbutt = PgButton("Quit Game", (800, 950), 50)
        self.quitbutt.connect(src.ONCLICKEVENT, lambda : sys.exit("Bye!"))
        self.quitbutt.connect(src.ENTERINGEVENT, lambda : self.quitbutt.switchbgcol(PgButton.HOVERCOL))
        self.quitbutt.connect(src.EXITINGEVENT, lambda : self.quitbutt.switchbgcol(PgButton.BGCOL))

        self.ngtitle = PgLabel("Select the maze", (350, 0), 60)

        self.backtomm = PgButton("Main Menu", (0, 950), 50)
        self.backtomm.connect(src.ONCLICKEVENT, self.mainpage)
        self.backtomm.connect(src.ENTERINGEVENT, lambda : self.backtomm.switchbgcol(PgButton.HOVERCOL))
        self.backtomm.connect(src.EXITINGEVENT, lambda : self.backtomm.switchbgcol(PgButton.BGCOL))
        
    def selectgame(self, filename):
        """Set the map filename"""
        self.fn = os.path.join(GAME_DIR, filename)
        self.mlstop = True

    def mainpage(self):
        """"Show the main menu page"""
        PgWidget.hideall(self.screen, self.BGCOL)
        self.title.show(self.screen)
        self.newbutt.show(self.screen)
        self.loadbutt.show(self.screen)
        self.quitbutt.show(self.screen)

    def menunewgame(self):
        """Show the menu page to choose a map"""
        PgWidget.hideall(self.screen, self.BGCOL)
        self.ngtitle.show(self.screen)
        self.backtomm.show(self.screen)

        filegames = os.listdir(GAME_DIR)
        if len(filegames) == 0:
            raise RuntimeError("Error! No game available!")

        for n, fg in enumerate(sorted(filegames)):
            gamebutt = PgButton(fg, (300, 100 + (n*60)), 50)
            gamebutt.connect(src.ONCLICKEVENT, lambda dfg=fg : self.selectgame(dfg))
            gamebutt.connect(src.ENTERINGEVENT, lambda bgc=PgButton.HOVERCOL, wgg=gamebutt : wgg.switchbgcol(bgc))
            gamebutt.connect(src.EXITINGEVENT, lambda bgc=PgButton.BGCOL, wgg=gamebutt : wgg.switchbgcol(bgc))
            gamebutt.show(self.screen)

    def menuloop(self):
        """The main loop for the menu and the game"""
        self.mainpage()

        while True:
            self.mlstop = False
            for event in pygame.event.get():
                if event.type == pyloc.QUIT:
                    sys.exit()
                elif event.type == pyloc.MOUSEBUTTONUP:
                    for ww in PgWidget.widget_list():
                        if ww.rect.collidepoint(event.pos):
                            ww.onclick_event()
                            break
                elif event.type == pyloc.MOUSEMOTION:
                    prevpos = (event.pos[0] - event.rel[0], event.pos[1] - event.rel[1])
                    for ww in PgWidget.widget_list():
                        if ww.rect.collidepoint(event.pos) and not ww.rect.collidepoint(prevpos):
                            ww.enter_event()
                            break
                        elif not ww.rect.collidepoint(event.pos) and ww.rect.collidepoint(prevpos):
                            ww.exit_event()
                            break
                elif event.type in [src.ONCLICKEVENT, src.ENTERINGEVENT, src.EXITINGEVENT]:
                    for ww in PgWidget.widget_list():
                        if ww._id == event.key_id:
                            for calls in ww.connectedcalls:
                                if calls[0] == event.type:
                                    calls[1]()
                                    break
                            else:
                                continue
                            break

            for ww in PgWidget.widget_list():
                ww.wupdate(self.screen)
            pygame.display.update()
            if self.mlstop:
                break

    def gameloop(self):
        while True:
            self.menuloop()
            if self.fn is not None:
                game = Maze(self.fn)
                game.mazeloop(self.screen)
