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

import sys
import os
import re
import numpy as np
import pygame

from src.mzgblocks import *


class Room:
    def __init__(self, rp, isgame):
        self.isgame = isgame
        self.roompos = rp
        self.allblocks = sprite.Group()
        self.walls = sprite.Group()
        self.ladders = sprite.Group()
        self.deathblocks = sprite.Group()
        self.bots = sprite.Group()
        self.doors = sprite.Group()
        self.keys = sprite.Group()
        self.screens = np.array([1, 1])

    def addelem(self, lstpar):
        bpos = list(map(int, lstpar[1:3]))
        if lstpar[0] in ['W', 'L', 'T']:
            bsize = list(map(int, lstpar[3:5]))
            if lstpar[0] == 'W':
                crblock = Wall(bpos, bsize)
                self.walls.add(crblock)
            elif lstpar[0] == 'L':
                crblock = Ladder(bpos, bsize)
                self.ladders.add(crblock)
            elif lstpar[0] == 'T':
                crblock = Deadlyblock(bpos, bsize)
                self.deathblocks.add(crblock)
        elif lstpar[0] == 'D':
            dooridx = int(lstpar[3])
            bsize = Door.rectsize
            crblock = Door(bpos, int(lstpar[3]), bool(int(lstpar[4])))
            self.doors.add(crblock)
        elif lstpar[0] == 'K':
            dooridx = list(map(int, lstpar[3:5]))
            bsize = Key.rectsize
            crblock = Key(bpos, dooridx)
            self.keys.add(crblock)
        elif lstpar[0] == 'B':
            coordinates = list(map(int, lstpar[3:]))
            bsize = EnemyBot.rectsize
            crblock = EnemyBot(bpos, self.isgame, coordinates)
            self.bots.add(crblock)
        else:
            raise RuntimeError("error during room construction: '{}'".format(' '.join(lstpar)))

        self.allblocks.add(crblock)
        
        #adjusting screens if needed
        maxx = ((bpos[0] + bsize[0]) // 1000)+1
        maxy = ((bpos[1] + bsize[1]) // 1000)+1
        if maxx > self.screens[0]:
            self.screens[0] = maxx
        if maxy > self.screens[1]:
            self.screens[1] = maxy

    def screenfrac(self, refblock):
        ix = refblock.aurect.x // 1000
        iy = refblock.aurect.y // 1000
        if ix < self.screens[0] and iy < self.screens[1]:
            return np.array([ix, iy])
        else:
            raise RuntimeError

    def isoffvalid(self, off):
        if not (0 <= off[0] < self.screens[0] and 0 <= off[1] < self.screens[1]):
            raise RuntimeError

    def hoveringsprites(self):
        return self.ladders.sprites() + self.doors.sprites() + self.keys.sprites()

    def alldestinations(self):
        return [dd.destination for dd in self.doors.sprites()]

    def alldoorsid(self):
        return [dd._id for dd in self.doors.sprites()]

    def getdoorref(self, idx):
        ref = None
        for dd in self.doors.sprites():
            if dd._id == idx:
                ref = dd
                break
        return ref

    def update(self, xoff, yoff):
        self.allblocks.update(xoff, yoff)

    def draw(self, sface):
        self.allblocks.draw(sface)

    def empty(self):
        for bb in self.allblocks.sprites():
            bb.kill()


class Maze:
    BGCOL = (0, 0, 0)

    def __init__(self, fn, isgame=True, loadmap=True):
        self.isgame = isgame
        self.filename = fn
        self.cursor = None
        self.croom = None
        self.cpp = None
        self.firstroom = None
        if loadmap:
            self.rooms = None
            self.initcounters()
            self.maploader()
        else:
            self.rooms = np.empty(shape=1, dtype=Room)

    def initcounters(self):
        Door.initcounter()
        Key.initcounter()
    
    def maploader(self):
        with open(self.filename) as fob:
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
                        elif lline[0] == 'IR' and len(lline) == 2:
                            self.firstroom = int(lline[1])
                        elif lline[0] == 'IP' and len(lline) == 3:
                            curspos = list(map(int, lline[1:]))
                        elif len(lline) >= 3:
                            self.rooms[ridx].addelem(lline)
                        else:
                            raise RuntimeError(f"error in map construction: {fl}")

        self.initcursor(curspos)
        self.croom = self.rooms[self.firstroom]

    def initcursor(self, cpos):
        self.cursor = Character(cpos)
        self.cursor.setforcefield(0.0, 200.0)

    def scrollscreen(self, screen):
        try:
            self.croom.isoffvalid(self.cpp)
        except RuntimeError:
            newev = pygame.event.Event(src.DEATHEVENT)
            pygame.event.post(newev)
            return
        screen.fill(self.BGCOL)
        self.croom.update(self.cpp[0], self.cpp[1])
        self.cursor.update(self.cpp[0], self.cpp[1])
        self.croom.draw(screen)

    def crossdoor(self, doorid, destination):
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
        blitnow = []
        for rr in self.rooms:
            for doorid in dooridlist:
                if doorid in rr.alldoorsid():
                    dooropening = rr.getdoorref(doorid)
                    dooropening.locked = False
                    if self.croom.roompos == rr.roompos:
                        blitnow.append(dooropening)
        return blitnow

    def mazeloop(self, screen):
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
                elif event.type == src.DEATHEVENT:
                    for rr in self.rooms:
                        rr.empty()
                    return
            
            if enterroom:
                self.cpp = self.croom.screenfrac(self.cursor)
                self.cursor.update(self.cpp[0], self.cpp[1])
                enterroom = False
                self.scrollscreen(screen)
                
            screen.fill(self.BGCOL, self.cursor.rect)
            for bot in self.croom.bots.sprites():
                screen.fill(self.BGCOL, bot.rect)

            #redrawing blocks where player or bots have passed
            for ldd in self.croom.hoveringsprites():
                for mvspr in self.croom.bots.sprites() + [self.cursor]:
                    if ldd.aurect.colliderect(mvspr.aurect):
                        screen.blit(ldd.image, ldd.rect)

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
                        break

            #checking if character is dying touching a deadly block or a bot
            for ltt in self.croom.deathblocks.sprites() + self.croom.bots.sprites():
                if ltt.aurect.colliderect(self.cursor.aurect):
                    ltt.death_event()
                    dying = True
                    break
            if dying:
                continue

            self.cursor.movecharacter(self.croom.walls, self.croom.ladders)
            screen.blit(self.cursor.image, self.cursor.rect)
            for bot in self.croom.bots.sprites():
                bot.movebot()
                screen.blit(bot.image, bot.rect)

            pygame.display.update()
            addcoord = self.cursor.insidesurf(screen)
            clock.tick(src.FPS)
            if addcoord is not None:
                self.cpp += addcoord
                self.scrollscreen(screen)
