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
import re
import numpy as np
import threading
import inspect

import pygame
from pygame import sprite
import pygame.locals as pyloc

import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter import messagebox

import src
src.ISGAME = False

from src.mzgrooms import Maze
from src.mzgblocks import Block
from src.mzgblocks import add_counter
from src.mzgscreen import editorarea

GAME_DIR = os.path.join(src.MAIN_DIR, '../gamemaps')

DOUBLECLICKTIME = 300

#userevent actions
ACT_REFRESH = 0 #no keyword
ACT_SCROLL = 1  #need keywords xoff, yoff
ACT_DELETEBLOCK = 2  #need keyword todelete
ACT_ADDBLOCK = 3 #need keyword line
ACT_MOVECURSOR = 4 #no keyword
ACT_STICKGRID = 5 #need keywords block, which


@add_counter
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
        super(ScrollBlock, self).__init__(next(self._idcounter), pos, rsize)
        self.image.fill((100, 200, 50))
        self.image.set_colorkey((0, 0, 0))
        self.direction = direction

    def scrolling_event(self):
        """Post a scrolling event into the pygame.event queue"""
        scrlev = pygame.event.Event(pyloc.USEREVENT, action=ACT_SCROLL, xoff=self.direction[0], yoff=self.direction[1])
        pygame.event.post(scrlev)


class DrawMaze(Maze):
    """The room container with additions for the editor

    child of mzgrooms.Maze. It uses predefined ScrollBlocks to scroll the room
    with the mouse. It's created by the App interface.
    """
    
    def __init__(self, fn):
        """Initialization:
        
        fn -- filename of the map to be load and used.
        """
        super(DrawMaze, self).__init__(fn, None, False)
        self.cpp = np.array([0, 0])
        self.scrollareas = pygame.sprite.Group()
        self.scrollareas.add(ScrollBlock([0, -20], [1000, 20], [0, -1]))
        self.scrollareas.add(ScrollBlock([1000, 0], [20, 1000], [1, 0]))
        self.scrollareas.add(ScrollBlock([0, 1000], [1000, 20], [0, 1]))
        self.scrollareas.add(ScrollBlock([-20, 0], [20, 1000], [-1, 0]))

    @property
    def croom(self):
        return super(DrawMaze, self).croom

    @croom.setter
    def croom(self, val):
        #cannot use super here, we want to override the parent behaviour
        self._croom = val

    def draw(self, screen, bgimage=None):
        """Draw the blocks on the screen"""
        self.croom.update(self.cpp[0], self.cpp[1])
        self.croom.draw(screen, self.cpp, bgimage)
        for bot in self.croom.bots.sprites():
            for mrk in bot.getmarkers():
                screen.blit(mrk.image, self.croom.area.corrpix_blit(mrk.rect))

        if self.cursor is not None and self.cursor.cridx == self.croom.roompos:
            self.cursor.update(self.cpp[0], self.cpp[1])
            screen.blit(self.cursor.image, self.croom.area.corrpix_blit(self.cursor.rect))

    def getallblocks(self, iroom):
        """Return a list of all the sprites in the current room"""
        markers = []
        for bot in iroom.bots.sprites():
            markers.extend(bot.getmarkers())
        return iroom.allblocks.sprites() + markers


class Blockinfo(tk.Frame):
    """Base interface for small box dialog, to let the user enter extra parameters of blocks

    Child of tk.Frame, use its childs. All of them must implement the getinfo method,
    returning a list of the extra parameters inputted by the user in the dialogs.
    """
    
    def __init__(self, parent):
        """Initialization"""
        super(Blockinfo, self).__init__(parent)

    def getinfo(self):
        """To be overriden: return a list of the extra parameters inputted by the user in the dialogs"""
        raise NotImplementedError


class Doorinfo(Blockinfo):
    """Small box dialog to let the user enter the extra parameters of a Door block.

    Child of Blockinfo.
    """
    
    def __init__(self, parent):
        """Initialization"""
        super(Doorinfo, self).__init__(parent)
        self.labelone = tk.Label(self, text="Destination door id")
        self.labelone.grid(row=0, column=0)
        self.doordest = tk.Spinbox(self, from_=0, to=10000)
        self.doordest.grid(row=1, column=0)

        self.lockvar = tk.IntVar()
        self.labeltwo = tk.Label(self, text="Is locked?")
        self.labeltwo.grid(row=0, column=1)
        self.islocked = tk.Checkbutton(self, variable=self.lockvar)
        self.islocked.grid(row=1, column=1)

    def getinfo(self):
        """Overriding method: return a list of the extra parameters"""
        return [int(self.doordest.get()), self.lockvar.get()]


class Keyinfo(Blockinfo):
    """Small box dialog to let the user enter the extra parameters of a Key block.

    Child of Blockinfo.
    """
    
    def __init__(self, parent):
        """Initialization"""
        super(Keyinfo, self).__init__(parent)
        self.labelone = tk.Label(self, text="Door's ids (separated by spaces)")
        self.labelone.grid(row=0, column=0)
        self.opened = tk.Entry(self)
        self.opened.grid(row=1, column=0)

    def getinfo(self):
        """Overriding method: return a list of the extra parameters"""
        try:
            res = list(map(int, self.opened.get().strip().split()))
        except ValueError as err:
            print("Error in setting ids of doors to be opened by the key: please insert integers!\n" + str(err))
            res = None
        return res


class EnemyBotinfo(Blockinfo):
    """Small box dialog to let the user enter the extra parameters of a Key block.

    Child of Blockinfo.
    """

    def __init__(self, parent):
        """Initialization"""
        super(EnemyBotinfo, self).__init__(parent)
        self.blockpos = parent.blockpos
        self.cpp = parent.cpp
        self.labelone = tk.Label(self, text="Number of marker to control bot's path")
        self.labelone.grid(row=0, column=0)
        self.nummarker = tk.Spinbox(self, from_=1, to=10000)
        self.nummarker.grid(row=1, column=0)

    def getinfo(self):
        """Overriding method: return a list of the extra parameters"""
        ux, uy = editorarea.pixtopos(self.cpp[0], self.cpp[1], editorarea.corrpix_comp(self.blockpos))
        ll = [(ux + (i*50), uy) for i in range(1, int(self.nummarker.get())+1)]
        return [el for sl in ll for el in sl]


class WindAreainfo(Blockinfo):
    """Small box dialog to let the user enter the extra parameters of a WindArea block.

    Child of Blockinfo.
    """

    windvalues = {"UP" : 0, "UP-RIGHT" : 1, "RIGHT" : 2, "DOWN-RIGHT" : 3, "DOWN" : 4, "DOWN-LEFT" : 5, "LEFT" : 6, "TOP-LEFT" : 7}
    windforces = {"LIGHT" : 1, "MODERATE" : 2, "STRONG" : 3, "VERY STRONG" : 4}

    def __init__(self, parent, iniwd=0, inistre=0, inivis=0):
        """Initialization"""
        super(WindAreainfo, self).__init__(parent)
        self.labeldir = tk.Label(self, text="Wind direction")
        self.labeldir.grid(row=0, column=0, sticky="ew")
        self.winddir = ttk.Combobox(self, values=list(self.windvalues.keys()))
        self.winddir.grid(row=0, column=1, sticky="ew")
        self.winddir.current(iniwd)
        
        self.labelstre = tk.Label(self, text="Wind strenght")
        self.labelstre.grid(row=1, column=0, sticky="ew")
        self.windstre = ttk.Combobox(self, values=list(self.windforces.keys()))
        self.windstre.grid(row=1, column=1, sticky="ew")
        self.windstre.current(inistre-1) #-1 because windforces start from 1

        self.visvar = tk.IntVar()
        self.visvar.set(inivis)
        self.windvis = tk.Checkbutton(self, text="Area visible?", variable=self.visvar)
        self.windvis.grid(row=2, column=0, columnspan=2, sticky="ew")

        self.labelinfo = tk.Label(self, text="NOTE: A moderate strength\nis equivalent to gravity")
        self.labelinfo.grid(row=3, column=0, columnspan=2, sticky="ew")

    def getinfo(self):
        """Overriding method: return a list of the extra parameters"""
        return [self.windvalues[self.winddir.get()], self.windforces[self.windstre.get()], self.visvar.get()]


class NewBlockDialog(tk.Toplevel):
    """Dialog interface to create a new block.

    Child of tkinter.Toplevel
    It open a dialog with a combobox of all block types, the user can choice
    one which will be added at the clicked position.
    """

    def _recoverblocks(obj):
        """Recover the block types from the module using reflection"""
        return inspect.isclass(obj) and issubclass(obj, Block) and obj.__name__ not in ['Block', 'Character', 'Marker']

    allblocks = list(name for name, obj in inspect.getmembers(src.mzgblocks, _recoverblocks))

    def __init__(self, parent, pos, roomcoord):
        """Initialization:
        
        parent -- parent widget
        pos -- 2-length list, x y coordinates of the top-left corner or the to-be-created block
        """
        super(NewBlockDialog, self).__init__(parent)
        self.blockpos = pos
        self.cpp = roomcoord
        self.title("New Block")
        self.label = tk.Label(self, text="Choose the type of block to add")
        self.label.grid(row=0, column=0, columnspan=4, sticky="ew")

        self.blocktypes = ttk.Combobox(self, values=self.allblocks + ['Door Set'])
        self.blocktypes.grid(row=1, column=0, columnspan=4, sticky="ew")
        self.blocktypes.current(0)
        self.blocktypes.bind("<<ComboboxSelected>>", self.showcustompanel)

        self.custompanel = None

        self.okbutton = tk.Button(self, text="Create block", command=lambda : self.choose(True))
        self.okbutton.grid(row=5, column=0)

        self.cancelbutton = tk.Button(self, text="Cancel", command=lambda : self.choose(False))
        self.cancelbutton.grid(row=5, column=3)

    def showcustompanel(self, event):
        """callback to be executed on combobox selection, shows a Blockinfo child"""
        infoblocks = {"Door" : Doorinfo, "Key" : Keyinfo, "EnemyBot" : EnemyBotinfo, "WindArea" : WindAreainfo}
        if self.custompanel is not None:
            self.custompanel.grid_forget()
        try:
            self.custompanel = infoblocks[self.blocktypes.get()](self)
            self.custompanel.grid(row=2, column=0, rowspan=3, columnspan=4, sticky="ew")
        except KeyError:
            self.custompanel = None

    def choose(self, value):
        """If value is True, create the block posting the ACT_ADDBLOCK signal to the pygame event system""" 
        if value:
            blocktype = self.blocktypes.get()
            if blocktype in self.allblocks:
                nid = next(getattr(src.mzgblocks, blocktype)._idcounter)
                idepos = [nid] + editorarea.pixtopos(self.cpp[0], self.cpp[1], *editorarea.corrpix_comp(self.blockpos))
                addparam = []
                if self.custompanel is not None:
                    extrapar = self.custompanel.getinfo()
                    if extrapar is None:
                        return
                    addparam.extend(extrapar)
                newline = getattr(src.mzgblocks, blocktype).reprlinenew(idepos, *addparam)
                newev = pygame.event.Event(pyloc.USEREVENT, action=ACT_ADDBLOCK, line=newline)
                pygame.event.post(newev)
            elif blocktype == 'Door Set':
                bltp = ['Door', 'Door', 'Key']
                nids = [next(src.mzgblocks.Door._idcounter), next(src.mzgblocks.Door._idcounter), next(src.mzgblocks.Key._idcounter)]
                params = [[[nids[0]] + list(self.blockpos), [nids[1], 1]],
                          [[nids[1]] + [self.blockpos[0]+50, self.blockpos[1]], [nids[0], 1]],
                          [[nids[2]] + [self.blockpos[0]+100, self.blockpos[1]], nids[0:2]]]
                for btp, prm in zip(bltp, params):
                    newline = getattr(src.mzgblocks, btp).reprlinenew(prm[0], *prm[1])
                    newev = pygame.event.Event(pyloc.USEREVENT, action=ACT_ADDBLOCK, line=newline)
                    pygame.event.post(newev)

        self.destroy()


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
        self.info = tk.Label(self, text="To move a block, move to\nthe destination room before\nclicking the button Move.")
        self.info.grid(row=0, column=0, sticky="ew")
        
        self.actbuttons = []
        for i, (key, entry) in enumerate(self.refblock.actionmenu.items()):
            bb = tk.Button(self, text=key, command=getattr(self, f"act_{entry}"))
            bb.grid(row=i+1, column=0, sticky="ew")
            self.actbuttons.append(bb)

    def act_delete(self):
        """Post the ACT_DELETEBLOCK signal to the pygame event system, to delete the selected block"""
        newev = pygame.event.Event(pyloc.USEREVENT, action=ACT_DELETEBLOCK, todelete=self.refblock)
        pygame.event.post(newev)
        self.destroy()

    def act_move(self):
        """Move select block to another room"""
        copyline = self.refblock.reprline()
        if copyline.startswith('IN'):
            newev = pygame.event.Event(pyloc.USEREVENT, action=ACT_MOVECURSOR)
            pygame.event.post(newev)
        else:
            addev = pygame.event.Event(pyloc.USEREVENT, action=ACT_ADDBLOCK, line=copyline)
            delev = pygame.event.Event(pyloc.USEREVENT, action=ACT_DELETEBLOCK, todelete=self.refblock)
            pygame.event.post(addev)
            pygame.event.post(delev)
        self.destroy()
        
    def act_addmarker(self):
        """Add a marker to a enemybot"""
        self.refblock.addmarker(self.refblock.aurect.x + 50, self.refblock.aurect.y)
        newev = pygame.event.Event(pyloc.USEREVENT, action=ACT_REFRESH)
        pygame.event.post(newev)

    def act_editwind(self):            
        """Edit windarea force options (calling another dialog)"""
        def callok(tp, wa):
            params = tp.infoarea.getinfo()
            wa._windpar[0] = params[0]
            wa._windpar[1] = params[1]
            wa.visible = params[2]
            newev = pygame.event.Event(pyloc.USEREVENT, action=ACT_REFRESH)
            pygame.event.post(newev)
            tp.destroy()

        def callclose(tp):
            tp.destroy()
        
        topdial = tk.Toplevel()
        topdial.title("Edit wind parameter")
        topdial.infoarea = WindAreainfo(topdial, self.refblock._windpar[0], self.refblock._windpar[1], self.refblock.visible)
        topdial.infoarea.grid(row=0, column=0, columnspan=2, sticky="ew")
        topdial.okbutton = tk.Button(topdial, text="Edit block", command=lambda : callok(topdial, self.refblock))
        topdial.okbutton.grid(row=1, column=0, sticky="ew")
        topdial.cancelbutton = tk.Button(topdial, text="Cancel", command=lambda : callclose(topdial))
        topdial.cancelbutton.grid(row=1, column=1, sticky="ew")


class GridSupport(src.PosManager):
    """Class to automate block resetting. Blocks stay sticked to a grid.

    Child of PosManager
    If defines the grid (horizontal and vertical axes) and provide the
    useful resetblock method to reset a block position and size such that
    it stay sticked to the closer grid lines.
    """

    GRIDSIZE = 10 #in arbitrary units
    GRIDCOL = (0, 100, 200)
    
    def __init__(self):
        """Initialization."""
        #no need to store an offset
        self.makegrid()

    def makegrid(self):
        self._xcs = np.arange(0, 1001, self.GRIDSIZE)
        self._ycs = np.arange(0, 1001, self.GRIDSIZE)
        
    def xcs(self, xoff):
        """Return x coordinates of the grid. xoff is the screen offset on x coordinate"""
        return (xoff*1000) + self._xcs

    def ycs(self, yoff):
        """Return y coordinates of the grid. yoff is the screen offset on y coordinate"""
        return (yoff*1000) + self._ycs

    def resetblock(self, off, block, issize):
        """Reset block position

        off - 2-length list, tuple or array, the (x, y) offset
        block - reference to the block to be reset.
        issise - if True, block size is modified, its position otherwise.
        """
        rx = block.aurect.right if issize else block.aurect.x
        ry = block.aurect.bottom if issize else block.aurect.y
        xshift = rx - self.xcs(off[0])
        yshift = ry - self.ycs(off[1])
        xcp = np.absolute(xshift).argmin()
        ycp = np.absolute(yshift).argmin()
        if issize:
            if block.aurect.width - xshift[xcp] == 0:
                xcp += 1
            if block.aurect.height - yshift[ycp] == 0:
                ycp += 1
            block.rsize = [block.aurect.width - xshift[xcp], block.aurect.height - yshift[ycp]]
        else:
            block.aurect.x -= xshift[xcp]
            block.aurect.y -= yshift[ycp]

    def drawonsurf(self, sface, clean=False):
        pass


class App(tk.Tk):
    """the editor container. Represents the top level class, contaning the editor.

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

        self.gridsupport = GridSupport()

        self.title("Maze Editor")
        self.newbutton = tk.Button(self, text="New map", command=self.newgame)
        self.newbutton.grid(row=0, column=0, sticky="ew", columnspan=2)

        self.loadbutton = tk.Button(self, text="Load map", command=self.loadgame)
        self.loadbutton.grid(row=0, column=2, sticky="ew", columnspan=2)

        self.savebutton = tk.Button(self, text="Save map", command=self.writegame)
        self.savebutton.grid(row=0, column=4, sticky="ew", columnspan=2)

        self.addroombutton = tk.Button(self, text="Add room", command=self.addroom)
        self.addroombutton.grid(row=1, column=0, sticky="ew", columnspan=3)

        self.delroombutton = tk.Button(self, text="Delete room", command=self.delroom)
        self.delroombutton.grid(row=1, column=3, sticky="ew", columnspan=3)

        self.nextroombutton = tk.Button(self, text="Show next room", command=lambda : self.showroom(1))
        self.nextroombutton.grid(row=2, column=0, sticky="ew", columnspan=3)

        self.prevroombutton = tk.Button(self, text="Show previous room", command=lambda : self.showroom(-1))
        self.prevroombutton.grid(row=2, column=3, sticky="ew", columnspan=3)

        self.gridflag = tk.IntVar()
        self.gridopt = tk.Checkbutton(self, text="Stick to the grid.", variable=self.gridflag, command=self.draw)
        self.gridopt.grid(row=3, column=1, sticky="ew")

        self.gridstep = tk.Spinbox(self, values=(10, 20, 50, 100), width=10, command=self.setgridstep)
        self.gridstep.grid(row=3, column=2, sticky="ew", columnspan=2)
        self.gridsupport.GRIDSIZE = self.gridstep.get()

        self.gridsteplb = tk.Label(self, text="Grid step")
        self.gridsteplb.grid(row=3, column=4, sticky="ew")

        self.infoarea = tk.Text(self, height=5)
        self.infoarea.grid(row=0, column=6, rowspan=3)
        self.infoarea.tag_configure("emph", foreground="red")
        self.infoarea.insert("1.0", f"Number of rooms: 0\n")        
        self.infoarea.insert("2.0", f"Current room: 0\n")
        self.infoarea.insert("3.0", f"Current area: 0, 0\n")
        self.infoarea.tag_add("emph", "1.17", "1.17lineend")
        self.infoarea.tag_add("emph", "2.14", "2.14lineend")
        self.infoarea.tag_add("emph", "3.14", "3.14lineend")
        self.infoarea.config(state=tk.DISABLED)

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
        newev = pygame.event.Event(pyloc.USEREVENT, action=ACT_REFRESH)
        pygame.event.post(newev)

    def loadgame(self):
        """Open the a map to edit it"""
        mazefile = askopenfilename(initialdir=GAME_DIR, title="Load file", filetypes=[("all files","*")])
        if len(mazefile) > 0:
            self.maze = DrawMaze(mazefile)
            newev = pygame.event.Event(pyloc.USEREVENT, action=ACT_REFRESH)
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
                sf.write(self.maze.cursor.reprline() + '\n')

    def addroom(self):
        """Add a new room to the maze"""
        if self.maze is not None:
            rid = len(self.maze.rooms)
            self.maze.rooms = np.append(self.maze.rooms, src.mzgrooms.Room(rid, False))
            self.updateinfoarea()
                
    def delroom(self):
        """Delete the shown room from the maze"""
        if self.maze is not None:
            if self.maze.cursor.cridx == self.maze.croom.roompos:
                messagebox.showinfo("WARNING", "Cannot delete a room of the character is inside.")
            else:
                answer = messagebox.askyesno("WARNING", "You are deleting the shown Room.\nThere is no going back.\nAre you sure?")
                if answer:
                    self.maze.rooms = np.delete(self.maze.rooms, self.maze.croom.roompos)
                    self.maze.croom = self.maze.rooms[0]
                    self.draw()
                    self.updateinfoarea(0)

    def showroom(self, off):
        """Select a room and show it, off is the offset from current shown room"""
        if self.maze is not None:
            idx = self.maze.croom.roompos + off
            if 0 <= idx < len(self.maze.rooms):
                self.maze.croom = self.maze.rooms[idx]
                self.draw()
                self.updateinfoarea(idx)

    def updateinfoarea(self, nroom=None):
        """Update the text area in the GUI to show current region of the room"""
        self.infoarea.config(state=tk.NORMAL)
        self.infoarea.delete("1.17", "1.17lineend")
        self.infoarea.insert("1.17", str(len(self.maze.rooms)))
        self.infoarea.tag_add("emph", "1.17", "1.17lineend")
        if nroom is not None:
            self.infoarea.delete("2.14", "2.14lineend")
            self.infoarea.insert("2.14", str(nroom+1))
            self.infoarea.tag_add("emph", "2.14", "2.14lineend")
        self.infoarea.delete("3.14", "3.14lineend")
        self.infoarea.insert("3.14", f"{self.maze.cpp[0]}, {self.maze.cpp[1]}\n")
        self.infoarea.tag_add("emph", "3.14", "3.14lineend")
        self.infoarea.config(state=tk.DISABLED)

    def blockdialog(self, slblock):
        """Open a BlockAction, slblock is the block affected"""
        dlg = BlockActions(self, slblock)

    def setgridstep(self):
        self.gridsupport.GRIDSIZE = int(self.gridstep.get())
        self.gridsupport.makegrid()
        self.draw()

    def draw(self):
        """Draw the screen, both grid (if needed) and blocks"""
        bgsurf = None
        if self.maze is not None:
            self.pygscreen.fill(self.maze.BGCOL)
        else:
            self.pygscreen.fill((0, 0, 0)) #black
        if self.gridflag.get():
            bgsurf = pygame.Surface((editorarea.aurect.width, editorarea.aurect.height))
            #pretending that offset is always zero when drawing #@@@ to be fixed
            for x in self.gridsupport.xcs(0):
                pygame.draw.line(bgsurf, self.gridsupport.GRIDCOL, editorarea.postopix(0, 0, x, 0), editorarea.postopix(0, 0, x, 1000))
            for y in self.gridsupport.ycs(0):
                pygame.draw.line(bgsurf, self.gridsupport.GRIDCOL, editorarea.postopix(0, 0, 0, y), editorarea.postopix(0, 0, 1000, y))
        if self.maze is not None:
            self.maze.draw(self.pygscreen, bgsurf)

    def pygameloop(self):
        """The editor main loop for the pygame part"""
        dbclock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pyloc.QUIT:
                    sys.exit()
                elif event.type == pyloc.USEREVENT:
                    if event.action == ACT_REFRESH:
                        self.updateinfoarea(self.maze.croom.roompos)
                    elif event.action == ACT_SCROLL:
                        fpos = self.maze.cpp + np.array([event.xoff, event.yoff])
                        if fpos[0] >= 0 and fpos[1] >= 0:
                            self.maze.cpp = fpos
                            self.updateinfoarea()
                    elif event.action == ACT_ADDBLOCK:
                        for bln in event.line.split('\n'):
                            lline = re.split('\s+', bln.strip())
                            newblock = self.maze.croom.addelem(lline)
                            if self.gridflag.get():
                                stickevpos = pygame.event.Event(pyloc.USEREVENT, action=ACT_STICKGRID, which=0, block=newblock)
                                pygame.event.post(stickevpos)
                                stickevsiz = pygame.event.Event(pyloc.USEREVENT, action=ACT_STICKGRID, which=1, block=newblock)
                                pygame.event.post(stickevsiz)
                    elif event.action == ACT_DELETEBLOCK:
                        event.todelete.kill()
                    elif event.action == ACT_MOVECURSOR:
                        self.maze.cursor.cridx = self.maze.croom.roompos
                    elif event.action == ACT_STICKGRID:
                        self.gridsupport.resetblock(self.maze.cpp, event.block, event.which)
                    else:
                        print(event.action)
                    self.draw()
                elif event.type == pyloc.KEYDOWN:
                    if event.key == pyloc.K_LCTRL and self.grabbed is not None and self.gridflag.get():
                        stickev = pygame.event.Event(pyloc.USEREVENT, action=ACT_STICKGRID, which=0, block=self.grabbed)
                        pygame.event.post(stickev)
                elif event.type == pyloc.KEYUP:
                    if event.key == pyloc.K_LCTRL and self.grabbed is not None and self.gridflag.get():
                        stickev = pygame.event.Event(pyloc.USEREVENT, action=ACT_STICKGRID, which=1, block=self.grabbed)
                        pygame.event.post(stickev)
                elif event.type == pyloc.MOUSEBUTTONDOWN and self.maze is not None:
                    self.grabbed = self.grabblock(event.pos)
                    if self.grabbed is not None and event.button == 3:
                        if len(self.grabbed.actionmenu) > 0:
                            self.blockdialog(self.grabbed)
                    elif self.grabbed is None and event.button == 1:
                        for scb in self.maze.scrollareas.sprites():
                            if scb.rect.collidepoint(event.pos):
                                break
                        else:
                            if dbclock.tick() < DOUBLECLICKTIME:
                                chooser = NewBlockDialog(self, event.pos, self.maze.cpp)
                elif event.type == pyloc.MOUSEBUTTONUP and self.maze is not None:
                    if self.grabbed is not None and self.gridflag.get():
                        wh = 1 if pygame.key.get_pressed()[pyloc.K_LCTRL] else 0
                        stickev = pygame.event.Event(pyloc.USEREVENT, action=ACT_STICKGRID, which=wh, block=self.grabbed)
                        pygame.event.post(stickev)
                    self.draw()
                    self.grabbed = None
                    for scb in self.maze.scrollareas.sprites():
                        if scb.rect.collidepoint(event.pos):
                            scb.scrolling_event()
                            break
                elif event.type == pyloc.MOUSEMOTION and self.maze is not None:
                    if event.buttons == (1, 0, 0) and self.grabbed is not None:
                        if pygame.key.get_pressed()[pyloc.K_LCTRL] and self.grabbed.resizable:
                            nw = self.grabbed.rsize[0] + event.rel[0]
                            nh = self.grabbed.rsize[1] + event.rel[1]
                            self.pygscreen.fill(self.maze.BGCOL, editorarea.corrpix_blit(self.grabbed.rect))
                            self.grabbed.rsize = [nw, nh]
                            self.grabbed.update(self.maze.cpp[0], self.maze.cpp[1])
                            self.pygscreen.blit(self.grabbed.image, editorarea.corrpix_blit(self.grabbed.rect))
                        else:
                            self.pygscreen.fill(self.maze.BGCOL, editorarea.corrpix_blit(self.grabbed.rect))
                            self.grabbed.aurect.x += event.rel[0]
                            self.grabbed.aurect.y += event.rel[1]
                            self.grabbed.update(self.maze.cpp[0], self.maze.cpp[1])
                            self.pygscreen.blit(self.grabbed.image, editorarea.corrpix_blit(self.grabbed.rect))

            pygame.display.update()
            
    def grabblock(self, mpos):
        """grab a block to perform basic actions on it (moving, resizing, or open the BlockActions dialog)"""
        corrpos = editorarea.corrpix_comp(mpos)
        bll = self.maze.getallblocks(self.maze.croom)
        if self.maze.cursor.cridx == self.maze.croom.roompos:
            bll.append(self.maze.cursor)
        
        for block in bll:
            if block.rect.collidepoint(corrpos):
                return block
        return None


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode(src.PosManager.screen_size())
    gui = App(screen)
    gui.geometry("500x500+10+10")
    gui.protocol("WM_DELETE_WINDOW", gui.on_closing)
    gui.mainloop()
