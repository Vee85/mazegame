#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  mzgrooms.py
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

"""Contains container classes of the fundamental blocks, used to build the maze.

Room -- the block container. It keeps all the blocks of a single room of the maze,
in separate sprite Groups according to their type, with functions to recover
useful information from the blocks.

Maze -- the room container. It's the maze, it manages the rooms, the player,
function to load a map and provides the main loop for the game and other useful functions
to manage the game.
"""


import sys
import os
import re
import io
import numpy as np
import pygame

from src.mzgblocks import *
from src.mzgscreen import mazearea, editorarea
from src import ISGAME

SAVE_DIR = os.path.join(src.MAIN_DIR, '../saves')


class Room:
    """the block container. Represent a room of the maze.

    Instances of this class (and their methods) should be managed by the Maze class.
    """

    if ISGAME:
        area = mazearea
    else:
        area = editorarea

    def __init__(self, rp, isgame):
        """Initialization:
        
        rp -- id of the room in the Maze, identify the position of the room in a list
        isgame -- boolean, if True the room is created by the game,
        if False is created by the editor
        """
        self.isgame = isgame
        self.roompos = rp
        self.allblocks = sprite.Group()
        self.walls = sprite.Group()
        self.ladders = sprite.Group()
        self.deathblocks = sprite.Group()
        self.bots = sprite.Group()
        self.doors = sprite.Group()
        self.keys = sprite.Group()
        self.windareas = sprite.Group()
        self.checkpoints = sprite.Group()
        self.screens = np.array([1, 1])

    def addelem(self, lstpar):
        """Parse a text line (lstpar argument) to create the corresponding block"""
        blid = int(lstpar[1])
        bpos = list(map(int, lstpar[2:4]))
        if lstpar[0] in ['W', 'L', 'T', 'F']:
            bsize = list(map(int, lstpar[4:6]))
            if lstpar[0] == 'W':
                crblock = Wall(blid, bpos, bsize)
                self.walls.add(crblock)
            elif lstpar[0] == 'L':
                crblock = Ladder(blid, bpos, bsize)
                self.ladders.add(crblock)
            elif lstpar[0] == 'T':
                crblock = Deadlyblock(blid, bpos, bsize)
                self.deathblocks.add(crblock)
            elif lstpar[0] == 'F':
                frc = list(map(int, lstpar[6:8]))
                crblock = WindArea(blid, bpos, bsize, frc, bool(int(lstpar[8])))
                self.windareas.add(crblock)
        elif lstpar[0] == 'D':
            bsize = Door.rectsize
            crblock = Door(blid, bpos, int(lstpar[4]), bool(int(lstpar[5])))
            self.doors.add(crblock)
        elif lstpar[0] == 'K':
            dooridx = list(map(int, lstpar[4:6]))
            bsize = Key.rectsize
            crblock = Key(blid, bpos, dooridx)
            self.keys.add(crblock)
        elif lstpar[0] == 'B':
            coordinates = list(map(int, lstpar[4:]))
            bsize = EnemyBot.rectsize
            crblock = EnemyBot(blid, bpos, coordinates)
            self.bots.add(crblock)
        elif lstpar[0] == 'C':
            bsize = Checkpoint.rectsize
            crblock = Checkpoint(blid, bpos)
            self.checkpoints.add(crblock)
        else:
            raise RuntimeError("error during room construction: '{}'".format(' '.join(lstpar)))

        self.allblocks.add(crblock)
        if self.isgame:
            next(crblock._idcounter)
        
        #adjusting screens if needed
        maxx = ((bpos[0] + bsize[0]) // 1000)+1
        maxy = ((bpos[1] + bsize[1]) // 1000)+1
        if maxx > self.screens[0]:
            self.screens[0] = maxx
        if maxy > self.screens[1]:
            self.screens[1] = maxy
        return crblock

    def offscreen(self, refblock):
        """Return the offset of the screen of a reference block 'refblock'.

        Rooms are bigger than the screen so when player moves the camera must follow it.
        The offset of the screen is a 2-length np.array contaning by how many "screen"
        the current block position is far from the top left corner of the room. 
        """
        ix = refblock.aurect.x // 1000
        iy = refblock.aurect.y // 1000
        if ix < self.screens[0] and iy < self.screens[1]:
            return np.array([ix, iy])
        else:
            raise RuntimeError

    def isoffvalid(self, off):
        """Check if the offset is valid, raise a RuntimeError if not.

        off -- the offset, a 2-length container for x and y offset (see offscreen method)
        Both numbers must be positive and smaller than the total size of the room.
        """
        if not (0 <= off[0] < self.screens[0] and 0 <= off[1] < self.screens[1]):
            raise RuntimeError

    def hoveringsprites(self):
        """Return a list with all the block sprites which can be crossed throught by the player"""
        return self.ladders.sprites() + self.doors.sprites() + self.keys.sprites() + self.windareas.sprites() + self.checkpoints.sprites()

    def alldoorsid(self):
        """Return a list with all the door id"""
        return [dd._id for dd in self.doors.sprites()]

    def alldestinations(self):
        """Return a list with all the door id destinations"""
        return [dd.destination for dd in self.doors.sprites()]

    def getdoorref(self, idx):
        """Return the door sprite corresponding to the given id"""
        ref = None
        for dd in self.doors.sprites():
            if dd._id == idx:
                ref = dd
                break
        return ref

    def update(self, xoff, yoff):
        """Update all sprite blocks"""
        self.allblocks.update(xoff, yoff)

    def draw(self, sface, off):
        """Draw all sprite blocks"""
        cnt = self.area.origin_area(off)
        self.area.image.fill((0, 0, 0))
        for bb in self.allblocks:
            if cnt.colliderect(bb.aurect):
                self.area.image.blit(bb.image, bb.rect)
        sface.blit(self.area.image, (self.area.aurect.x, self.area.aurect.y))

    def empty(self):
        """Kill all sprite blocks"""
        for bb in self.allblocks.sprites():
            bb.kill()


class Maze:
    """the room container. Represent the top level class of the game.

    Not only Maze holds all the rooms, it also provides the method to move the sprites
    and to play. It's created by the menu TopLev interface.
    """
    
    BGCOL = (0, 0, 0)
    gravity = np.array([0.0, 200.0])

    def __init__(self, fn, loadfile=None, isgame=True):
        """Initialization:
        
        fn -- filename of the map to be load and used.
        isgame -- boolean, if True the maze is created by the game,
        if False is created by the editor
        """
        self.isgame = isgame
        self.filename = fn
        self.chpfilename = os.path.join(SAVE_DIR, "checkpoint")
        self.rooms = None
        self.cursor = None
        self._croom = None
        self.cpp = None
        self.firstroom = None
        self.initcounters()
        self.maploader()

        #loading game (starting not from beginning if a proper loadfile is given or checkpoint
        if loadfile is None:
            #new game
            try:
                os.remove(self.chpfilename)
            except FileNotFoundError:
                pass
        elif loadfile == -1:
            #using checkpoint
            self.loadchp()
        else:
            #using save file
            pass

    @property
    def croom(self):
        return self._croom

    @croom.setter
    def croom(self, val):
        """property setter for the current room, val could be a room instance or an integer (the room id)"""
        if isinstance(val, Room):
            self._croom = val
        elif isinstance(val, int):
            for room in self.rooms:
                if room.roompos == val:
                    self._croom = room
                    break
            else:
                raise RuntimeError("Error while setting a room! Given integer does not correspond to a valid id room in the maze!")
        else:
            raise RuntimeError("Error while setting a room! Invalid value.")

        if self.cursor is not None:
            self.cursor.cridx = self._croom.roompos

    def initcounters(self):
        """Reset the id generators of the block types which have an id"""
        Door.initcounter()
        Key.initcounter()
        EnemyBot.initcounter()
        Marker.initcounter()
    
    def maploader(self):
        """Load a map, parsing the textfile or creating the default (almost empty) map"""
        if self.filename is not None:
            streamer = open(self.filename)
        else:
            streamer = io.StringIO("NR 1\nR 0\nIN 0 50 50\n")
        
        with streamer as fob:
            #searching the first valid line: map dimension
            for fl in fob:
                sfl = fl.strip()
                if len(sfl) > 0:
                    if sfl[0] != '#':
                        numroomline = sfl.split()
                        if numroomline[0] == 'NR' and len(numroomline) == 2:
                            self.rooms = np.empty(shape=int(numroomline[1]), dtype=Room)
                            break
                        else:
                            raise RuntimeError(f"error in map construction: {fl}")

            #reading the rest of the file, building the rooms
            for fl in fob:
                sfl = fl.strip()
                if len(sfl) > 0:
                    if sfl[0] != '#':
                        lline = re.split('\s+', sfl)
                        if lline[0] == 'R' and len(lline) == 2:
                            ridx = int(lline[1])
                            self.rooms[ridx] = Room(ridx, self.isgame)
                        elif lline[0] == 'IN':
                            self.firstroom = int(lline[1])
                            curspos = list(map(int, lline[2:]))
                        elif len(lline) >= 4:
                            self.rooms[ridx].addelem(lline)
                        else:
                            raise RuntimeError(f"error in map construction: {fl}")

        self.initcursor(curspos)
        self.croom = self.rooms[self.firstroom]

    def initcursor(self, cpos):
        """Create and initialize the player"""
        self.cursor = Character(cpos, self.firstroom)
        self.cursor.setforcefield(self.gravity)

    def scrollscreen(self, screen):
        """Draw the next portion of the room on the screen"""
        try:
            self.croom.isoffvalid(self.cpp)
        except RuntimeError:
            newev = pygame.event.Event(src.DEATHEVENT)
            pygame.event.post(newev)
            return
        screen.fill(self.BGCOL) #@@@ this line may be removed later since we use a surface for the game
        self.croom.update(self.cpp[0], self.cpp[1])
        self.cursor.update(self.cpp[0], self.cpp[1])
        self.croom.draw(screen, self.cpp)

    def crossdoor(self, doorid, destination):
        """Enter in a door: player position is reset to the destination door.

        doorid -- the id of the door in which the player is entering
        destination -- the id of the door from which the player exit
        """
        roomidx = self.croom.roompos
        if destination < 0:
            sys.exit("You win!")
        for ridx, rr in enumerate(self.rooms):
            if doorid in rr.alldestinations():
                self.croom = self.rooms[ridx]
                break
        for nrldd in self.croom.doors:
            if nrldd.destination == doorid:
                self.cursor.aurect.x = nrldd.aurect.x
                self.cursor.aurect.y = nrldd.aurect.y
                break

    def keytaken(self, keyid, dooridlist):
        """Take a key and open the corresponding doors.

        keyid -- the id of the key taken by the player
        dooridlist -- the list of all the doors
        """
        blitnow = []
        for rr in self.rooms:
            for doorid in dooridlist:
                if doorid in rr.alldoorsid():
                    dooropening = rr.getdoorref(doorid)
                    dooropening.locked = False
                    if self.croom.roompos == rr.roompos:
                        blitnow.append(dooropening)
        return blitnow

    def savepoint(self, checkpoint_id):
        """Write on the disc a save file; checkpoint_id is the id of the Checkpoint block."""
        print("checkpoint!") #@@@ to be substituded with a message in game
        with open(self.chpfilename, 'w') as chpf:
            chpf.write(f"{self.croom.roompos}\n{checkpoint_id}\n")

    def loadchp(self):
        """Load game to checkpoint (character position and item taken)"""
        if os.path.isfile(self.chpfilename):
            with open(self.chpfilename) as chpf:
                idroom = int(next(chpf).strip())
                idcp = int(next(chpf).strip())

            self.croom = idroom
            for chpbl in self.croom.checkpoints:
                if chpbl._id == idcp:
                    self.cursor.aurect.x = chpbl.aurect.x
                    self.cursor.aurect.y = chpbl.aurect.y
                    break

    def mazeloop(self, screen):
        """The game main loop. screen is the pygame.display"""
        enterroom = True
        dying = False
        clock = pygame.time.Clock()
        while True:
            kup = False
            for event in pygame.event.get():
                if event.type == pyloc.QUIT:
                    sys.exit()
                elif event.type == pyloc.KEYDOWN:
                    if event.key == pyloc.K_UP:
                        kup = True
                elif event.type == src.ENTERDOOREVENT:
                    self.crossdoor(event.door_id, event.destination)
                elif event.type == src.TAKEKEYEVENT:
                    drawdoors = self.keytaken(event.key_id, event.openeddoor)
                    for drd in drawdoors:
                        screen.blit(drd.image, drd.rect)
                elif event.type == src.CHECKPEVENT:
                    self.savepoint(event.key_id)
                elif event.type == src.ENTERINGEVENT:
                    self.cursor.setforcefield(self.gravity + event.wind)
                elif event.type == src.EXITINGEVENT:
                    self.cursor.setforcefield(self.gravity)
                elif event.type == src.DEATHEVENT:
                    for rr in self.rooms:
                        rr.empty()
                    return
            
            if enterroom:
                self.cpp = self.croom.offscreen(self.cursor)
                self.cursor.update(self.cpp[0], self.cpp[1])
                enterroom = False
                cnt = self.croom.area.origin_area(self.cpp)
                self.scrollscreen(screen)

            #deleting moving elements (to animate the movement)
            screen.fill(self.BGCOL, self.cursor.rect)
            for bot in self.croom.bots.sprites():
                screen.fill(self.BGCOL, bot.rect)

            #redrawing blocks where player or bots have passed
            for hob in self.croom.hoveringsprites():
                for mvspr in self.croom.bots.sprites() + [self.cursor]:
                    if hob.aurect.colliderect(mvspr.aurect):
                        innerarea = mvspr.rect.copy()
                        innerarea.x -= hob.rect.x
                        innerarea.y -= hob.rect.y
                        screen.blit(hob.image, mvspr.rect, area=innerarea)

            #checking if the character is entering a checkpoint
            if kup:
                for chp in self.croom.checkpoints:
                    if chp.aurect.contains(self.cursor.aurect):
                        chp.checkp_event()
                        break

            #checking if the character is entering in a door
            if kup:
                for ldd in self.croom.doors:
                    if ldd.aurect.contains(self.cursor.aurect) and not ldd.locked:
                        ldd.entering_event()
                        enterroom = True
                        break
                if enterroom:
                    continue

            #checking if the character is taking a key
            if kup:
                for lkk in self.croom.keys:
                    if lkk.aurect.contains(self.cursor.aurect) and not lkk.taken:
                        lkk.takingkey_event()
                        lkk.taken = True
                        screen.blit(lkk.image, lkk.rect)
                        break

            #adjusting force field if entering or leaving a windarea
            if WindArea.cursorinside is None:
                for wnd in self.croom.windareas:
                    if wnd.aurect.contains(self.cursor.aurect):
                        WindArea.cursorinside = wnd
                        wnd.entering_wind_event()
                        break
            else:
                if not WindArea.cursorinside.aurect.contains(self.cursor.aurect):
                    WindArea.cursorinside.exiting_wind_event()
                    WindArea.cursorinside = None

            #checking if character is dying touching a deadly block or a bot
            for ltt in self.croom.deathblocks.sprites() + self.croom.bots.sprites():
                if ltt.aurect.colliderect(self.cursor.aurect):
                    ltt.death_event()
                    dying = True
                    break
            if dying:
                continue

            #handling movement drawing - bots moved but drawn only if inside ScreenArea.
            self.cursor.movecharacter(self.croom.walls, self.croom.ladders)
            screen.blit(self.cursor.image, self.cursor.rect)
            for bot in self.croom.bots.sprites():
                bot.movebot()
                if cnt.contains(bot.aurect):
                    screen.blit(bot.image, bot.rect)

            pygame.display.update()
            addcoord = self.cursor.insidearea()
            clock.tick(src.FPS)
            if addcoord is not None:
                self.cpp += addcoord
                self.scrollscreen(screen)
                cnt = self.croom.area.origin_area(self.cpp)


