#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  mazeditor.py
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
import numpy as np
import pygame
from pygame import sprite
import pygame.locals as pyloc
import tkinter as tk
from tkinter.filedialog import askopenfilename, asksaveasfilename
import threading

import src
from src.mzgrooms import Maze
from src.mzgblocks import Block

GAME_DIR = os.path.join(src.MAIN_DIR, '../gamemaps')

#userevent actions
ACT_NEW = 0
ACT_LOAD = 1
ACT_SCROLL = 2  #need keywords xoff, yoff
ACT_DELETEBLOCK = 3  #need keyword todelete


class ScrollBlock(Block):
    def __init__(self, pos, rsize, direction):
        super(ScrollBlock, self).__init__(pos, rsize)
        self.image.fill((0, 0, 0))
        self.image.set_colorkey((0, 0, 0))
        self.direction = direction

    def scrolling_event(self):
        scrlev = pygame.event.Event(pyloc.USEREVENT, action=ACT_SCROLL, xoff=self.direction[0], yoff=self.direction[1])
        pygame.event.post(scrlev)


class DrawMaze(Maze):
    def __init__(self, fn, loadmap):
        super(DrawMaze, self).__init__(fn, False, loadmap)
        self.cpp = np.array([0, 0])
        self.scrollareas = pygame.sprite.Group()
        self.scrollareas.add(ScrollBlock([0, -20], [1000, 20], [0, -1]))
        self.scrollareas.add(ScrollBlock([1000, 0], [20, 1000], [1, 0]))
        self.scrollareas.add(ScrollBlock([0, 1000], [1000, 20], [0, 1]))
        self.scrollareas.add(ScrollBlock([-20, 0], [20, 1000], [-1, 0]))

    def draw(self, screen):
        screen.fill(self.BGCOL)
        self.croom.update(self.cpp[0], self.cpp[1])
        self.croom.draw(screen)
        for bot in self.croom.bots.sprites():
            for mrk in bot.getmarkers():
                screen.blit(mrk.image, mrk.rect)

        if self.cursor is not None:
            self.cursor.update(self.cpp[0], self.cpp[1])
            screen.blit(self.cursor.image, self.cursor.rect)

    def getallblocks(self, iroom):
        markers = []
        for bot in iroom.bots.sprites():
            markers.extend(bot.getmarkers())
        return iroom.allblocks.sprites() + markers


class BlockActions(tk.Toplevel):
    def __init__(self, parent, refblock):
        super(BlockActions, self).__init__(parent)
        self.refblock = refblock
        self.title("Edit Block")
        self.geometry("200x50+10+10")

        self.actbuttons = []
        for entry in self.refblock.actionmenu:
            bb = tk.Button(self, text=entry, command=getattr(self, f"act_{entry}"))
            bb.pack(side="top")
            self.actbuttons.append(bb)

    def act_delete(self):
        newev = pygame.event.Event(pyloc.USEREVENT, action=ACT_DELETEBLOCK, todelete=self.refblock)
        pygame.event.post(newev)
        self.destroy()


class App(tk.Tk):
    def __init__(self, pygscreen):
        super(App, self).__init__()
        self.pygscreen = pygscreen
        self.grabbed = None
        self.maze = None
        self.mazefile = None

        self.title("Maze Editor")
        self.newbutton = tk.Button(self, text="New", command=self.sendtopyg)
        self.newbutton.pack(side="top")

        self.loadbutton = tk.Button(self, text="Load", command=self.loadgame)
        self.loadbutton.pack(side="top")

        self.savebutton = tk.Button(self, text="Save", command=self.writegame)
        self.savebutton.pack(side="top")

        thr = threading.Thread(target=self.pygameloop)
        thr.start()

    def on_closing(self):
        closeev = pygame.event.Event(pyloc.QUIT)
        pygame.event.post(closeev)
        self.destroy()

    def loadgame(self):
        mazefile = askopenfilename(initialdir=GAME_DIR, title="Load file", filetypes=[("all files","*")])
        if mazefile is not None:
            self.maze = DrawMaze(mazefile, True)
            newev = pygame.event.Event(pyloc.USEREVENT, action=ACT_LOAD)
            pygame.event.post(newev)

    def writegame(self):
        mazefile = asksaveasfilename(initialdir=GAME_DIR, title="Save file", filetypes=[("all files","*")])
        if mazefile is not None:
            with open(mazefile, 'w') as sf:
                sf.write(f"NR {str(len(self.maze.rooms))}\n")
                for rm in self.maze.rooms:
                    sf.write(f"R {rm.roompos}\n")
                    for block in rm.allblocks.sprites():
                        sf.write(block.reprline() + '\n')
                sf.write("\nIR " + str(self.maze.firstroom) + '\n')
                sf.write(self.maze.cursor.reprline() + '\n')

    def blockdialog(self, slblock):
        dlg = BlockActions(self, slblock)

    def pygameloop(self):
        while True:
            for event in pygame.event.get():
                if event.type == pyloc.QUIT:
                    sys.exit()
                elif event.type == pyloc.USEREVENT:
                    if event.action == ACT_LOAD:
                        self.maze.draw(self.pygscreen)
                    elif event.action == ACT_SCROLL:
                        self.maze.cpp += np.array([event.xoff, event.yoff])
                        self.maze.draw(self.pygscreen)
                    elif event.action == ACT_DELETEBLOCK:
                        event.todelete.kill()
                        self.maze.draw(self.pygscreen)
                    else:
                        print(event.action)
                elif event.type == pyloc.MOUSEBUTTONDOWN:
                    self.grabbed = self.grabblock(event.pos)
                    if self.grabbed is not None and event.button == 3:
                        if len(self.grabbed.actionmenu) > 0:
                            self.blockdialog(self.grabbed)
                elif event.type == pyloc.MOUSEBUTTONUP:
                    self.maze.draw(self.pygscreen)
                    self.grabbed = None
                    for scb in self.maze.scrollareas.sprites():
                        if scb.rect.collidepoint(event.pos):
                            scb.scrolling_event()
                            break
                elif event.type == pyloc.MOUSEMOTION:
                    if self.grabbed is not None:
                        if event.buttons == (1, 0, 0):
                            pressed = pygame.key.get_pressed()
                            if pressed[pyloc.K_LCTRL] and self.grabbed.resizable:
                                nw = self.grabbed.rsize[0] + event.rel[0]
                                nh = self.grabbed.rsize[1] + event.rel[1]
                                self.pygscreen.fill(self.maze.BGCOL, self.grabbed.rect)
                                self.grabbed.rsize = [nw, nh]
                                self.grabbed.update(self.maze.cpp[0], self.maze.cpp[1])
                                self.pygscreen.blit(self.grabbed.image, self.grabbed.rect)
                            else:
                                self.pygscreen.fill(self.maze.BGCOL, self.grabbed.rect)
                                self.grabbed.aurect.x += event.rel[0]
                                self.grabbed.aurect.y += event.rel[1]
                                self.grabbed.update(self.maze.cpp[0], self.maze.cpp[1])
                                self.pygscreen.blit(self.grabbed.image, self.grabbed.rect)
                            
            pygame.display.update()
            
    def sendtopyg(self):
        newev = pygame.event.Event(pyloc.USEREVENT, action=339)
        pygame.event.post(newev)

    def grabblock(self, mpos):
        bll = self.maze.getallblocks(self.maze.croom)
        if self.maze.firstroom == self.maze.croom.roompos:
            bll.append(self.maze.cursor)
        
        for block in bll:
            if block.rect.collidepoint(mpos):
                return block
        return None


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode(src.PosManager.screen_size())
    gui = App(screen)
    gui.geometry("500x500+10+10")
    gui.protocol("WM_DELETE_WINDOW", gui.on_closing)
    gui.mainloop()
