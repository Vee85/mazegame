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
    '''Base class for all widgets do not use it directly, use its children'''
    _idcounter = count(0)
    allwidgets = sprite.Group()
    
    def __init__(self, surf, pos):
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
        PgWidget._idcounter = count(0)

    @staticmethod
    def widget_list(shownonly=True):
        if shownonly:
            return [ww for ww in PgWidget.allwidgets.sprites() if ww._shown]
        else:
            return PgWidget.allwidgets.sprites()

    def show(self, sscr, loadscreen=False):
        #loadscreen useful for child classes who override this method
        #ssrc must be the screen surface
        sscr.blit(self.image, self.pos)
        self._shown = True

    def wupdate(self, sscr):
        if self.update:
            self.show(sscr, False)
            self.update = False

    @staticmethod
    def hideall(sscr, bgc):
        #ssrc must be the screen surface
        sscr.fill(bgc)
        for ww in PgWidget.widget_list():
            ww._shown = False
    
    def enter_event(self):
        newev = pygame.event.Event(src.ENTERINGEVENT, key_id=self._id)
        pygame.event.post(newev)

    def exit_event(self):
        newev = pygame.event.Event(src.EXITINGEVENT, key_id=self._id)
        pygame.event.post(newev)

    def onclick_event(self):
        newev = pygame.event.Event(src.ONCLICKEVENT, key_id=self._id)
        pygame.event.post(newev)

    def connect(self, eventtype, callback):
        conn = (eventtype, callback)
        self.connectedcalls.append(conn)

    @staticmethod
    def clear_widgets():
        PgWidget.allwidgets.empty()


class PgLabel(PgWidget):
    def __init__(self, labtext, pos, textheight, font=None, textcolor=(255, 255, 255)):
        self.text = labtext
        self.font = font
        mfont = pygame.font.Font(self.font, self.sizetopix(0, textheight)[1])
        surftext = mfont.render(self.text, True, textcolor)
        super(PgLabel, self).__init__(surftext, self.postopix(0, 0, pos))


class PgButton(PgWidget):
    BGCOL = (0, 0, 0)
    HOVERCOL = (100, 100, 100)
    TEXTCOL = (255, 255, 255)
    def __init__(self, buttext, pos, textheight, font=None):
        self.text = buttext
        self.font = font
        self.textheight = textheight
        wgsurf = self.drawbutton(self.BGCOL)
        super(PgButton, self).__init__(wgsurf, self.postopix(0, 0, pos))

    def drawbutton(self, bgc):
        mfont = pygame.font.Font(self.font, self.sizetopix(0, self.textheight)[1])
        surftext = mfont.render(self.text, True, self.TEXTCOL)
        surfbutton = pygame.Surface([surftext.get_width(), surftext.get_height()])
        surfbutton.fill(bgc)
        surfbutton.blit(surftext, (0, 0))
        return surfbutton

    def switchbgcol(self, bgc):
        self.image = self.drawbutton(bgc)
        self.update = True

    def show(self, ssrc, loadscreen=True):
        if loadscreen:
            self.switchbgcol(self.BGCOL)
        super(PgButton, self).show(ssrc)


class TopLev:
    BGCOL = (0, 0, 0)
    
    def __init__(self, screen):
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
        self.fn = os.path.join(GAME_DIR, filename)
        self.mlstop = True

    def mainpage(self):
        PgWidget.hideall(self.screen, self.BGCOL)
        self.title.show(self.screen)
        self.newbutt.show(self.screen)
        self.loadbutt.show(self.screen)
        self.quitbutt.show(self.screen)

    def menunewgame(self):
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
