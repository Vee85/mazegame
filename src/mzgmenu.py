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

"""Contains the TopLevel class of the whole game.

TopLev -- The class holding the menu, connecting the callbacks and starting the game.
"""

import sys
import os
import pygame
from pygame import sprite
import pygame.locals as pyloc

import src
from src.mzgwidgets import *
from src.mzgscreen import ScreenArea, InfoArea
from src.mzgrooms import Maze


GAME_DIR = os.path.join(src.MAIN_DIR, '../gamemaps')

class TopLev:
    """the game container. Represent the top level class, contaning the menu and the game.

    menuloop method is the main loop, other methods of this class are called inside the main loop.
    """
    
    BGCOL = (0, 0, 0)
    MENUPAGES = {'main':'main', 'ng':'newgame', 'go':'gameover'}
    
    def __init__(self, screen):
        """Initialization:

        screen -- the pygame.display surface
        """
        self.fn = None
        self.lfile = None
        self.mlstop = False
        self.screen = screen

        #area for the main menu
        self.menuarea = ScreenArea(0, 0, 1000, 1000, 20, 20)
        #area where game info are shown
        self.ginfoarea = InfoArea(self.screen, 800, 0, 200, 800, 10, 10)

        self.title = PgLabel(self.menuarea, "MAZEGAME", (300, 0), 100)

        self.newbutt = PgButton(self.menuarea, "New Game", (100, 150), 50)
        self.newbutt.connect(src.ONCLICKEVENT, lambda : self.show_menupage('ng'))
        self.newbutt.connect(src.ENTERINGEVENT, lambda : self.newbutt.switchbgcol(PgButton.HOVERCOL))
        self.newbutt.connect(src.EXITINGEVENT, lambda : self.newbutt.switchbgcol(PgButton.BGCOL))

        self.loadbutt = PgButton(self.menuarea, "Load Game", (600, 150), 50)
        self.loadbutt.connect(src.ONCLICKEVENT, lambda : print(self.loadbutt.text))
        self.loadbutt.connect(src.ENTERINGEVENT, lambda : self.loadbutt.switchbgcol(PgButton.HOVERCOL))
        self.loadbutt.connect(src.EXITINGEVENT, lambda : self.loadbutt.switchbgcol(PgButton.BGCOL))

        self.quitbutt = PgButton(self.menuarea, "Quit Game", (800, 950), 50)
        self.quitbutt.connect(src.ONCLICKEVENT, lambda : sys.exit("Bye!"))
        self.quitbutt.connect(src.ENTERINGEVENT, lambda : self.quitbutt.switchbgcol(PgButton.HOVERCOL))
        self.quitbutt.connect(src.EXITINGEVENT, lambda : self.quitbutt.switchbgcol(PgButton.BGCOL))

        self.ngtitle = PgLabel(self.menuarea, "Select the maze", (350, 0), 60)

        self.backtomm = PgButton(self.menuarea, "Main Menu", (0, 950), 50)
        self.backtomm.connect(src.ONCLICKEVENT, lambda : self.show_menupage('main'))
        self.backtomm.connect(src.ENTERINGEVENT, lambda : self.backtomm.switchbgcol(PgButton.HOVERCOL))
        self.backtomm.connect(src.EXITINGEVENT, lambda : self.backtomm.switchbgcol(PgButton.BGCOL))

        self.golab = PgLabel(self.menuarea, "GAME OVER!", (400, 400), 60)
        self.gosublab = PgLabel(self.menuarea, "Do you want to continue?", (350, 500), 40)

        self.yesbutt = PgButton(self.menuarea, "YES", (350, 600), 40)
        self.yesbutt.connect(src.ONCLICKEVENT, self.continuegame)
        self.yesbutt.connect(src.ENTERINGEVENT, lambda : self.yesbutt.switchbgcol(PgButton.HOVERCOL))
        self.yesbutt.connect(src.EXITINGEVENT, lambda : self.yesbutt.switchbgcol(PgButton.BGCOL))

        self.nobutt = PgButton(self.menuarea, "NO", (650, 600), 40)
        self.nobutt.connect(src.ONCLICKEVENT, lambda : self.show_menupage('main'))
        self.nobutt.connect(src.ENTERINGEVENT, lambda : self.nobutt.switchbgcol(PgButton.HOVERCOL))
        self.nobutt.connect(src.EXITINGEVENT, lambda : self.nobutt.switchbgcol(PgButton.BGCOL))

    def show_menupage(self, page):
        """Call the proper function to show a page of the menu"""
        PgWidget.hideall(self.menuarea, self.BGCOL)
        getattr(self, 'menupage_' + self.MENUPAGES[page])()
        self.screen.blit(self.menuarea.image, self.menuarea.origin_area(np.array([0, 0])).get_rect())

    def menupage_main(self):
        """"Show the main menu page"""
        self.title.show()
        self.newbutt.show()
        self.loadbutt.show()
        self.quitbutt.show()

    def menupage_newgame(self):
        """Show the menu page to choose a map"""
        self.ngtitle.show()
        self.backtomm.show()

        filegames = os.listdir(GAME_DIR)
        validgames = [f for f in filegames if f.endswith("xml")]
        if len(validgames) == 0:
            raise RuntimeError("Error! No game available!")

        for n, fg in enumerate(sorted(validgames)):
            gamebutt = PgButton(self.menuarea, fg, (300, 100 + (n*60)), 50)
            gamebutt.connect(src.ONCLICKEVENT, lambda dfg=fg : self.selectgame(dfg))
            gamebutt.connect(src.ENTERINGEVENT, lambda bgc=PgButton.HOVERCOL, wgg=gamebutt : wgg.switchbgcol(bgc))
            gamebutt.connect(src.EXITINGEVENT, lambda bgc=PgButton.BGCOL, wgg=gamebutt : wgg.switchbgcol(bgc))
            gamebutt.show()

    def menupage_gameover(self):
        """Show the game over page"""
        self.golab.show()
        self.gosublab.show()
        self.yesbutt.show()
        self.nobutt.show()
        self.quitbutt.show()

    def selectgame(self, filename):
        """Set the map filename"""
        self.fn = os.path.join(GAME_DIR, filename)
        self.mlstop = True

    def continuegame(self):
        self.lfile = -1
        self.mlstop = True

    def menuloop(self, showpage='main'):
        """The main loop for the menu and the game"""
        self.show_menupage(showpage)

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
        mpage = 'main'
        while True:
            self.menuloop(mpage)
            if self.fn is not None:
                game = Maze(self.fn, self.lfile)
                game.iarea = self.ginfoarea
                game.mazeloop(self.screen)
                mpage = 'go'
