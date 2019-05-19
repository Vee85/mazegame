#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  mzgclasses.py
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

import os
import math
from itertools import count
import numpy as np
import pygame
from pygame import sprite
import pygame.locals as pyloc

import src

IMAGE_DIR = os.path.join(src.MAIN_DIR, '../images')


class Block(sprite.Sprite, src.PosManager):
    '''Base class for all block, do not use it directly, use its children'''
    resizable = True
    actionmenu = ["delete"]
    
    def __init__(self, pos, rsize, bg=None):
        super(Block, self).__init__()
        self.image = pygame.Surface(self.sizetopix(rsize))
        self.aurect = src.FlRect(pos[0], pos[1], rsize[0], rsize[1])
        self.bg = bg
        self.fillimage()

        #place block to its coordinates
        self.update(0, 0)

    def fillimage(self):
        if self.bg is None:
            pass
        elif isinstance(self.bg, (tuple, list)):
            self.image.fill(self.bg)
        elif isinstance(self.bg, pygame.Surface):
            subim = self.bg.convert()
            for i in range(0, self.rsize[0], subim.get_rect().width):
                for j in range(0, self.rsize[1], subim.get_rect().height):
                    self.image.blit(subim, (i, j))
        else:
            raise RuntimeError("Wrong initialization parameter.")

    #prepare drawing, shift blocks to be in the screen
    def update(self, xoff, yoff):
        self.rect = self.recttopix(xoff, yoff, self.aurect.getRect())

    @property
    def rsize(self):
        return [self.aurect.width, self.aurect.height]

    @rsize.setter
    def rsize(self, newsize):
        if self.resizable:
            nwpxsize = self.sizetopix(newsize) #@@@this should not be resolution dependent. How to?
            if any([i <= 2 for i in nwpxsize]):
                return
            self.aurect.width = newsize[0]
            self.aurect.height = newsize[1]
            self.image = pygame.transform.scale(self.image, nwpxsize)
            self.fillimage()

    def reprline(self):
        return f"  {self.label} {self.aurect.x} {self.aurect.y} {self.aurect.width} {self.aurect.height}"

    def collidinggroup(self, group):
        return [sp for sp in group.sprites() if self.aurect.colliderect(sp.aurect)]
        

class Marker(Block):
    resizable = False
    label = 'M'
    _idcounter = count(0)
    BGCOL = (100, 100, 100)
    
    def __init__(self, pos, rsize, ref, isgame=True):
        self._id = next(self._idcounter)
        self.ref = ref
        if isgame:
            bg = None
        else:
            bg = self.BGCOL
        super(Marker, self).__init__(pos, rsize, bg)
        if not isgame:
            text = f"{self.ref}.{self._id}"
            mfont = pygame.font.Font(None, self.sizetopix(0, self.rsize[1])[1])
            surftext = mfont.render(text, True, (255, 0, 0))
            self.image.blit(surftext, (0, 0))

    @staticmethod
    def resetcounter():
        Marker._idcounter = count(0)

    def reprline(self):
        pass


class Wall(Block):
    label = 'W'
    BGCOL = (255, 255, 255)
    
    def __init__(self, pos, rsize):
        super(Wall, self).__init__(pos, rsize, self.BGCOL)


class Ladder(Block):
    label = 'L'
    BGIMAGE = pygame.image.load(os.path.join(IMAGE_DIR, "ladderpattern.png"))

    def __init__(self, pos, rsize):
        super(Ladder, self).__init__(pos, rsize, self.BGIMAGE)
        

class Door(Block):
    resizable = False
    label = 'D'
    _idcounter = count(0)
    rectsize = [50, 50]
    LDOOR = pygame.image.load(os.path.join(IMAGE_DIR, "lockeddoor.png"))
    LOCKEDDOOR = pygame.transform.scale(LDOOR, src.PosManager.sizetopix(rectsize))
    ODOOR = pygame.image.load(os.path.join(IMAGE_DIR, "opendoor.png"))
    OPENDOOR = pygame.transform.scale(ODOOR, src.PosManager.sizetopix(rectsize))
    LEXIT = pygame.image.load(os.path.join(IMAGE_DIR, "lockedexit.png"))
    LOCKEDEXIT = pygame.transform.scale(LEXIT, src.PosManager.sizetopix(rectsize))
    OEXIT = pygame.image.load(os.path.join(IMAGE_DIR, "openexit.png"))
    OPENEXIT = pygame.transform.scale(OEXIT, src.PosManager.sizetopix(rectsize))

    def __init__(self, pos, doorid, lock):
        super(Door, self).__init__(pos, self.rectsize)
        self._id = next(self._idcounter)
        self.destination = doorid
        self.locked = bool(lock)

    @staticmethod
    def initcounter():
        Door._idcounter = count(0)

    @property
    def locked(self):
        return self._locked

    @locked.setter
    def locked(self, boolvalue):
        self._locked = boolvalue
        self.showicon()

    def showicon(self):
        if self.destination >= 0:
            if self.locked:
                self.image.blit(self.LOCKEDDOOR.convert(), [0, 0])
            else:
                self.image.blit(self.OPENDOOR.convert(), [0, 0])
        else:
            if self.locked:
                self.image.blit(self.LOCKEDEXIT.convert(), [0, 0])
            else:
                self.image.blit(self.OPENEXIT.convert(), [0, 0])
        
    def entering_event(self):
        newev = pygame.event.Event(src.ENTERDOOREVENT, door_id=self._id, destination=self.destination)
        pygame.event.post(newev)

    def reprline(self):
        ilock = 1 if self.locked else 0
        return f"  {self.label} {self.aurect.x} {self.aurect.y} {self.destination} {ilock}"


class Key(Block):
    resizable = False
    label = 'K'
    _idcounter = count(0)
    rectsize = [50, 50]
    RAWIMKEY = pygame.image.load(os.path.join(IMAGE_DIR, "key.png"))
    IMKEY = pygame.transform.scale(RAWIMKEY, src.PosManager.sizetopix(rectsize))

    def __init__(self, pos, dooridlist):
        super(Key, self).__init__(pos, self.rectsize)
        self._id = next(self._idcounter)
        self.whoopen = dooridlist
        self.taken = False

    @staticmethod
    def initcounter():
        Key._idcounter = count(0)

    @property
    def taken(self):
        return self._taken

    @taken.setter
    def taken(self, boolvalue):
        self._taken = boolvalue
        self.showicon()

    def showicon(self):
        if self.taken:
            self.image.fill((0, 0, 0))
        else:
            self.image.blit(self.IMKEY.convert(), [0, 0])
    
    def takingkey_event(self):
        newev = pygame.event.Event(src.TAKEKEYEVENT, key_id=self._id, openeddoor=self.whoopen)
        pygame.event.post(newev)

    def reprline(self):
        return f"  {self.label} {self.aurect.x} {self.aurect.y} " + " ".join(map(str, self.whoopen))
        

class Deadlyblock(Block):
    label = 'T'
    BGCOL = (0, 0, 255)

    def __init__(self, pos, rsize):
        super(Deadlyblock, self).__init__(pos, rsize, self.BGCOL)

    def death_event(self):
        newev = pygame.event.Event(src.DEATHEVENT)
        pygame.event.post(newev)

    #inherited reprline from Block are fine


class EnemyBot(Block):
    resizable = False
    label = 'B'
    _idcounter = count(0)
    rectsize = [30, 30]
    BGCOL = (0, 255, 0)
    speed = 150

    def __init__(self, pos, isgame, *coordlist):
        self._id = next(self._idcounter)
        Marker.resetcounter()
        coordpoints = [crd for crd in src.pairextractor(*coordlist)] + [pos]
        self.pathmarkers = sprite.Group([Marker(cppos, self.rectsize, self._id, isgame) for cppos in coordpoints])
        super(EnemyBot, self).__init__(pos, self.rectsize, self.BGCOL)
        self.setspeed()
        if not isgame:
            text = str(self._id)
            mfont = pygame.font.Font(None, self.sizetopix(0, self.rsize[1])[1])
            surftext = mfont.render(text, True, (255, 0, 0))
            self.image.blit(surftext, (0, 0))
        
    def reprline(self):
        flattencoords = [i for pp in self.getmarkers() for i in [pp.aurect.x, pp.aurect.y]]
        return f"  {self.label} {self.aurect.x} {self.aurect.y} " + " ".join(map(str, flattencoords))

    def getmarkers(self):
        return self.pathmarkers.sprites()[:-1]

    def update(self, xoff, yoff):
        self.off = [xoff, yoff]
        super(EnemyBot, self).update(xoff, yoff)
        for mrk in self.pathmarkers.sprites():
            mrk.update(xoff, yoff)

    def death_event(self):
        newev = pygame.event.Event(src.DEATHEVENT)
        pygame.event.post(newev)

    def setspeed(self):
        try:
            curmarkerrect = self.pathmarkers.sprites()[self._ipm].aurect
            self._ipm += 1
        except AttributeError:
            curmarkerrect = self.pathmarkers.sprites()[-1].aurect
            self._ipm = 0
            
        if self._ipm == len(self.pathmarkers.sprites()):
            self._ipm = 0

        self.nextrect = self.pathmarkers.sprites()[self._ipm].aurect
        
        vecdist = src.rectdistance(self.nextrect, curmarkerrect)
        angle = np.arctan2(vecdist[1], vecdist[0])
        self.curspeed = np.array([self.speed*np.cos(angle), self.speed*np.sin(angle)])

    def movebot(self):
        cvdist = src.rectdistance(self.nextrect, self.aurect)
        moddist = np.linalg.norm(cvdist)
        if moddist >= (self.speed * src.TPF):
            self.aurect.x += self.curspeed[0] * src.TPF
            self.aurect.y += self.curspeed[1] * src.TPF
            self.rect = self.recttopix(self.off[0], self.off[1], self.aurect)
        else:
            self.aurect.x = self.pathmarkers.sprites()[self._ipm].aurect.x
            self.aurect.y = self.pathmarkers.sprites()[self._ipm].aurect.y
            self.setspeed()


class Character(Block):
    rectsize = [20, 20]
    CURSORCOL = (255, 0, 0)
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3
    JUMP = 4
    resizable = False
  
    def __init__(self, pos):
        super(Character, self).__init__(pos, self.rectsize, self.CURSORCOL)
        self.current_direction = set()
        self.touchplane = False

        #space unit is arbitrary (screen size = 1000), time unit is second
        #velocity value (on user movement)
        self.speed = 125
        self.jumpspeed = 250
        #velocity increment
        self.dvx = 0
        self.dvy = 0
        #acceleration
        self.ax = 0
        self.ay = 0

    def reprline(self):
        return f"IP {self.aurect.x} {self.aurect.y}"

    def update(self, xoff, yoff):
        self.off = [xoff, yoff]
        super(Character, self).update(xoff, yoff)
            
    def insidesurf(self, sface):
        if sface.get_rect().contains(self.rect):
            return None
        else:
            if self.rect.top < sface.get_rect().top:
                return np.array([0, -1])
            elif self.rect.left < sface.get_rect().left:
                return np.array([-1, 0])
            elif self.rect.bottom > sface.get_rect().bottom:
                return np.array([0, 1])
            elif self.rect.right > sface.get_rect().right:
                return np.array([1, 0])
      
    def getdirmove(self):
        pressed = pygame.key.get_pressed()
        if pressed[pyloc.K_UP]:
            self.current_direction.add(Character.UP)
        if pressed[pyloc.K_DOWN]:
            self.current_direction.add(Character.DOWN)
        if pressed[pyloc.K_RIGHT]:
            self.current_direction.add(Character.RIGHT)
        if pressed[pyloc.K_LEFT]:
            self.current_direction.add(Character.LEFT)
        if pressed[pyloc.K_SPACE]:
            if not self.touchplane:
                self.current_direction.add(Character.JUMP)

    def setforcefield(self, x, y=None):
        if y is None:
            if isinstance(x, (tuple, list)):
                self.ax = x[0]
                self.ay = x[1]
            else:
                raise RuntimeError("Wrong initialization parameter.")
        else:
            self.ax = x
            self.ay = y

    def applyforce(self):
        self.dvx += self.ax * src.TPF
        self.dvy += self.ay * src.TPF

    def movecharacter(self, groupwalls, groupladders):
        dsp = np.zeros(2)
        #applying force only if not on a ladder
        ladderspr = self.collidinggroup(groupladders)
        if len(ladderspr) == 0:
            self.applyforce()
        else:
            self.dvx = 0
            self.dvy = 0
            
        self.getdirmove()
        #checking x movement
        if len(self.current_direction) > 0:
            if self.LEFT in self.current_direction:
                dsp[0] += -1 * self.speed * src.TPF
            if self.RIGHT in self.current_direction:
                dsp[0] += self.speed * src.TPF

        dsp[0] += self.dvx * src.TPF
        self.aurect = self.aurect.move((dsp[0], 0))

        #checking x collisions with walls
        collspr = self.collidinggroup(groupwalls)
        if len(collspr) > 0:
            for w in collspr:
                if self.aurect.left < w.aurect.right and dsp[0] < 0:
                    self.aurect.left = w.aurect.right
                elif self.aurect.right > w.aurect.left and dsp[0] > 0:
                    self.aurect.right = w.aurect.left
            if src.checksign(self.ax) == src.checksign(dsp[0]):
                self.dvx = 0

        #checking y movement, possible on ladders only
        ladderspr = self.collidinggroup(groupladders)
        if len(ladderspr) > 0:
            if self.touchplane:
                self.touchplane = False
            if len(self.current_direction) > 0:
                if self.UP in self.current_direction:
                    dsp[1] += -1 * self.speed * src.TPF
                if self.DOWN in self.current_direction:
                    dsp[1] += self.speed * src.TPF

        #checking y movement due to jumping
        if len(self.current_direction) > 0:
            if self.JUMP in self.current_direction:
                dsp[1] += -1 * self.jumpspeed * src.TPF

        dsp[1] += self.dvy * src.TPF
        self.aurect = self.aurect.move(0, dsp[1])
        
        #checking y collisions with walls
        collspr = self.collidinggroup(groupwalls)
        if len(collspr) > 0:
            for w in collspr:
                if self.aurect.top < w.aurect.bottom and dsp[1] < 0:
                    self.aurect.top = w.aurect.bottom
                elif self.aurect.bottom > w.aurect.top and dsp[1] > 0:
                    self.aurect.bottom = w.aurect.top
            if src.checksign(self.ay) == src.checksign(dsp[1]):
                self.touchplane = False
            else:
                self.touchplane = True
            self.dvy = 0

        self.current_direction.clear()
        self.rect = self.recttopix(self.off[0], self.off[1], self.aurect)

