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

"""Main script to create the game editor. Also contains dedicated classes.

Use this file as executable to start the editor.
The editor uses a tkinter interface to provide the commands to create the map,
and a pygame display to manipulate the blocks.
"""


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
ACT_LOAD = 0
ACT_SCROLL = 1  #need keywords xoff, yoff
ACT_DELETEBLOCK = 2  #need keyword todelete


class ScrollBlock(Block):
    """An invisible block, used to define a clickable area to move the camera.

    Children of Block. Can be of any size but not resizable. Used to emit
    a scrolling event to move the camera and draw the next section of the room.
    Used only by the editor. 
    """

    resizable = False
    
    def __init__(self, pos, rsize, direction):
        """Initialization:
        
        pos -- two-length list with x, y coordinates of top-left corner of the rectangle
        rsize -- two-length list with width and height of the rectangle
        direction -- two-length list with x and y offset: by how much "screen" the camera must be moved
        e.g. [0, 1] to move by one screen down
        """
        super(ScrollBlock, self).__init__(pos, rsize)
        self.image.fill((0, 0, 0))
        self.image.set_colorkey((0, 0, 0))
        self.direction = direction

    def scrolling_event(self):
        """Post a scrolling event into the pygame.event queue"""
        scrlev = pygame.event.Event(pyloc.USEREVENT, action=ACT_SCROLL, xoff=self.direction[0], yoff=self.direction[1])
        pygame.event.post(scrlev)


class DrawMaze(Maze):
    """The room container with additions for the editor

    child of mzgrooms.Maze. Uses predefined ScrollBlocks to scroll the room
    with the mouse. It's created by the App interface.
    """
    
    def __init__(self, fn):
        """Initialization:
        
        fn -- filename of the map to be load and used.
        """
        super(DrawMaze, self).__init__(fn, False)
        self.cpp = np.array([0, 0])
        self.scrollareas = pygame.sprite.Group()
        self.scrollareas.add(ScrollBlock([0, -20], [1000, 20], [0, -1]))
        self.scrollareas.add(ScrollBlock([1000, 0], [20, 1000], [1, 0]))
        self.scrollareas.add(ScrollBlock([0, 1000], [1000, 20], [0, 1]))
        self.scrollareas.add(ScrollBlock([-20, 0], [20, 1000], [-1, 0]))

    def draw(self, screen):
        """Draw the screen"""
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
        """Return a list of all the sprites in the current room"""
        markers = []
        for bot in iroom.bots.sprites():
            markers.extend(bot.getmarkers())
        return iroom.allblocks.sprites() + markers


class BlockActions(tk.Toplevel):
    """Dialog interface to allow actions on a block on the screen.

    Child of tkinter.Toplevel
    It open a dialog with all the actions available for a block type
    Its method are binded as callbacks for the displayed buttons.
    """
    def __init__(self, parent, refblock):
        """Initialization:
        
        parent -- parent widget
        refblock -- block on which the action is performed
        """
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
    """the editor container. Represent the top level class, contaning the editor.

    Child of tkinter.Tk
    It uses threading to allow the tkinter GUI and the pygame display and mainloop to work
    at the same time.
    pygameloop method is the main loop for the pygame part, other methods of this class
    are called inside the main loop.
    """
    
    def __init__(self, pygscreen):
        """Initialization:

        pygscreen -- the pygame.display surface
        """
        super(App, self).__init__()
        self.pygscreen = pygscreen
        self.grabbed = None
        self.maze = None
        self.mazefile = None

        self.title("Maze Editor")
        self.newbutton = tk.Button(self, text="New", command=self.newgame)
        self.newbutton.pack(side="top")

        self.loadbutton = tk.Button(self, text="Load", command=self.loadgame)
        self.loadbutton.pack(side="top")

        self.savebutton = tk.Button(self, text="Save", command=self.writegame)
        self.savebutton.pack(side="top")

        thr = threading.Thread(target=self.pygameloop)
        thr.start()

    def on_closing(self):
        """Post the quit event to the pygame system event and close the tkinter GUI"""
        closeev = pygame.event.Event(pyloc.QUIT)
        pygame.event.post(closeev)
        self.destroy()

    def newgame(self):
        """Open the default initial map to create a new map"""
        self.maze = DrawMaze(None)
        newev = pygame.event.Event(pyloc.USEREVENT, action=ACT_LOAD)
        pygame.event.post(newev)

    def loadgame(self):
        """Open the a map to edit it"""
        mazefile = askopenfilename(initialdir=GAME_DIR, title="Load file", filetypes=[("all files","*")])
        if len(mazefile) > 0:
            self.maze = DrawMaze(mazefile)
            newev = pygame.event.Event(pyloc.USEREVENT, action=ACT_LOAD)
            pygame.event.post(newev)

    def writegame(self):
        """Save the current map in a file, ready to be played"""
        mazefile = asksaveasfilename(initialdir=GAME_DIR, title="Save file", filetypes=[("all files","*")])
        if len(mazefile) > 0:
            with open(mazefile, 'w') as sf:
                sf.write(f"NR {str(len(self.maze.rooms))}\n")
                for rm in self.maze.rooms:
                    sf.write(f"R {rm.roompos}\n")
                    for block in rm.allblocks.sprites():
                        sf.write(block.reprline() + '\n')
                sf.write("\nIR " + str(self.maze.firstroom) + '\n')
                sf.write(self.maze.cursor.reprline() + '\n')

    def blockdialog(self, slblock):
        """Open a BlockAction, slblock is the block affected"""
        dlg = BlockActions(self, slblock)

    def pygameloop(self):
        """the editor main loop for the pygame part"""
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
            
    def grabblock(self, mpos):
        """grab a block to perform basic actions on it (moving, resizing, or open the BlockActions dialog)"""
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
