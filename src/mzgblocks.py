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

"""Contains all classes defining the blocks, the fundamental elements of the game.

Block -- a base class defining a common interface for all blocks.
To not be used directly, all types of block are derived from it.

Marker -- an invisible block, used to mark a position on the screen.
Used as an intermediate position for EnemyBot movements.

Wall -- a solid block, can be used as floor, roof, or vertical wall.

Ladder -- a ladder, can be crossed and climbed to reach high platforms.

DeadlyBlock -- a block (any size) which should not be touched.

Door -- A door. Door comes in pairs, defining a sort of tunnel between
two places of the same room or to another room of the maze.

Key -- A key to open the locked doors.

EnemyBot -- A small moving block which should not be touched.

Character -- The cursor controlled by the player.
"""

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
    '''Base interface for all sprite block types, do not use it directly, use its children

    Children of pygame.sprite.Sprite and src.PosManager. The methods are:
    fillimage -- fill the image with the bg color or mosaic tile
    update -- update pygame.Rect with the current position / size
    reprline -- return text line of the block in map file format (used to create a map by the editor)
    collidinggroup -- return other sprites of a group colliding with this sprite
     
    It has also the following property:
    risze -- get or set the size of the block, if resizable
    '''
    
    resizable = True
    actionmenu = ["delete"]
    
    def __init__(self, pos, rsize, bg=None):
        """Initialization:
        
        pos -- two-length list with x, y coordinates of top-left corner of the rectangle
        rsize -- two-length list with width and height of the rectangle
        bg -- background color (3-length RGB tuple) or a pygame.Surface representing a tile
        """
        super(Block, self).__init__()
        self.image = pygame.Surface(self.sizetopix(rsize))
        self.aurect = src.FlRect(pos[0], pos[1], rsize[0], rsize[1])
        self.bg = bg
        self.fillimage()

        #place block to its coordinates
        self.update(0, 0)

    def fillimage(self):
        """Fill the image with the bg color or mosaic tile.

        Return nothing, raise a RuntimeError if an invalid instance has been
        stored as the 'bg' argument.
        """
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
        """Create or update the 'rect' attribute with a pygame.Rect with the current position / size"""
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
        """Return text line of the block in map file format (used to create a map by the editor

        This is a basic format holding a label and the PyRect values x, y, width, height.
        Is fine for basic blocks, more complex blocks need to override it with custom representation lines.
        """
        return f"  {self.label} {self.aurect.x} {self.aurect.y} {self.aurect.width} {self.aurect.height}"

    def collidinggroup(self, group):
        """Return other sprites of a group colliding with this sprite"""
        return [sp for sp in group.sprites() if self.aurect.colliderect(sp.aurect)]
        

class Marker(Block):
    """An invisible, any size but not resizable block, used to mark a position on the screen.

    Children of Block. Markers have an id incremented by 1 each time a new Marker
    is created, but can be resetted by the initcounter method.
    """
    
    resizable = False
    label = 'M'
    _idcounter = count(0)
    BGCOL = (100, 100, 100)
    
    def __init__(self, pos, rsize, ref, isgame=True):
        """Initialization:
        
        pos -- two-length list with x, y coordinates of top-left corner of the rectangle
        rsize -- two-length list with width and height of the rectangle
        ref -- reference to another Block which uses this Marker
        isgame -- boolean value, allows extra actions depending if the class is called
        by the game or by the editor.
        """
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
    def initcounter():
        """Staticmethod to reset the id generator"""
        Marker._idcounter = count(0)

    def reprline(self):
        """Override method of base class. Markers do not need a text line"""
        pass


class Wall(Block):
    """A solid wall of any size, can be used as floor, roof, or vertical wall.

    Children of Block.
    """
    
    label = 'W'
    BGCOL = (255, 255, 255)
    
    def __init__(self, pos, rsize):
        """Initialization:
        
        pos -- two-length list with x, y coordinates of top-left corner of the rectangle
        rsize -- two-length list with width and height of the rectangle
        """
        super(Wall, self).__init__(pos, rsize, self.BGCOL)


class Ladder(Block):
    """A ladder can be of any size. Can be crossed and climbed to reach high platforms.

    Children of Block.
    """
    
    label = 'L'
    BGIMAGE = pygame.image.load(os.path.join(IMAGE_DIR, "ladderpattern.png"))

    def __init__(self, pos, rsize):
        """Initialization:
        
        pos -- two-length list with x, y coordinates of top-left corner of the rectangle
        rsize -- two-length list with width and height of the rectangle
        """
        super(Ladder, self).__init__(pos, rsize, self.BGIMAGE)

        
class Deadlyblock(Block):
    """A block (any size) which should not be touched. Is game over.

    Children of Block. Create a death event if the player collides with it.
    """

    label = 'T'
    BGCOL = (0, 0, 255)

    def __init__(self, pos, rsize):
        """Initialization:
        
        pos -- two-length list with x, y coordinates of top-left corner of the rectangle
        rsize -- two-length list with width and height of the rectangle
        """
        super(Deadlyblock, self).__init__(pos, rsize, self.BGCOL)

    def death_event(self):
        """Post a deathevent into the pygame.event queue"""
        newev = pygame.event.Event(src.DEATHEVENT)
        pygame.event.post(newev)


class Door(Block):
    """A fixed size block, it represents one extremity of a passage.

    Children of Block. A Door has a numeric id, and holds the numeric id of
    another Door instance: the other end of the passage. It's game developer duty
    to create both Doors and assign the correct reference (the editor can help).
    Door have a property 'locked' to get / set if the door is open or closed and switch
    the corresponding icon on status change.
    Door is also used for the exit of the maze (winning the game). It works the same,
    but the icon is gold instead of white. Exit do not have a corresponding door.
    """
    
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
        """Initialization:
        
        pos -- two-length list with x, y coordinates of top-left corner of the rectangle
        doorid -- the id of the other end of the passage (the destination door).
        lock -- boolean or anythin that can be casted to boolean. If true the door is locked.
        """
        super(Door, self).__init__(pos, self.rectsize)
        self._id = next(self._idcounter)
        self.destination = doorid
        self.locked = bool(lock)

    @staticmethod
    def initcounter():
        """Staticmethod to reset the id generator"""
        Door._idcounter = count(0)

    @property
    def locked(self):
        return self._locked

    @locked.setter
    def locked(self, boolvalue):
        self._locked = boolvalue
        self.showicon()

    def showicon(self):
        """Show / switch the icon door locked / door open"""
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
        """Post an enterdoorevent into the pygame.event queue"""
        newev = pygame.event.Event(src.ENTERDOOREVENT, door_id=self._id, destination=self.destination)
        pygame.event.post(newev)

    def reprline(self):
        """Override method of base class, adding custom informations"""
        ilock = 1 if self.locked else 0
        return f"  {self.label} {self.aurect.x} {self.aurect.y} {self.destination} {ilock}"


class Key(Block):
    """A fixed size block, it represents a key to open a specific door.

    Children of Block. A Key has a numeric id and holds the numeric id of one or more Doors.
    If the key is taken, the Door(s) are opened. It's game developer duty to check that
    the key holds the ids of two connected Door (the game editor can help).
    The idea is that the same Key should open both sides of the passage, but things
    can be arranged differently.
    A Key can be set to open the exit Door, too.
    Key have a property 'taken' to get / set if the key has been taken.
    """
    
    resizable = False
    label = 'K'
    _idcounter = count(0)
    rectsize = [50, 50]
    RAWIMKEY = pygame.image.load(os.path.join(IMAGE_DIR, "key.png"))
    IMKEY = pygame.transform.scale(RAWIMKEY, src.PosManager.sizetopix(rectsize))

    def __init__(self, pos, dooridlist):
        """Initialization:
        
        pos -- two-length list with x, y coordinates of top-left corner of the rectangle
        dooridlist --  a list of the door ids which the key opens.
        """
        super(Key, self).__init__(pos, self.rectsize)
        self._id = next(self._idcounter)
        self.whoopen = dooridlist
        self.taken = False

    @staticmethod
    def initcounter():
        """Staticmethod to reset the id generator"""
        Key._idcounter = count(0)

    @property
    def taken(self):
        return self._taken

    @taken.setter
    def taken(self, boolvalue):
        self._taken = boolvalue
        self.showicon()

    def showicon(self):
        """Show / hide the icon of the key"""
        if self.taken:
            self.image.fill((0, 0, 0))
        else:
            self.image.blit(self.IMKEY.convert(), [0, 0])
    
    def takingkey_event(self):
        """Post a takekeyevent into the pygame.event queue"""
        newev = pygame.event.Event(src.TAKEKEYEVENT, key_id=self._id, openeddoor=self.whoopen)
        pygame.event.post(newev)

    def reprline(self):
        """Override method of base class, adding custom informations"""
        return f"  {self.label} {self.aurect.x} {self.aurect.y} " + " ".join(map(str, self.whoopen))
        

class EnemyBot(Block):
    """A fixed size block, it represents a enemy moving on a prefixed path. 

    Children of Block. A EnemyBot has a numeric id and moves at fixed speed in the room.
    Markers are used to determine the path: the bot moves from one marker to the next
    in a straight line, returns at the starting point and restart in a loop.
    If the player touches them, it's game over.
    """
    
    resizable = False
    label = 'B'
    _idcounter = count(0)
    rectsize = [30, 30]
    BGCOL = (0, 255, 0)
    speed = 150

    def __init__(self, pos, isgame, *coordlist):
        """Initialization:
        
        pos -- two-length list with x, y coordinates of top-left corner of the rectangle
        isgame -- boolean value, allows extra actions depending if the class is called
        *coordlist -- variadic, flat list of x y coordinates, used to create the Markers. Each pair
        represent the top left corner of the Marker rectangle.
        """
        self._id = next(self._idcounter)
        Marker.initcounter()
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
        """Override method of base class, adding custom informations"""
        flattencoords = [i for pp in self.getmarkers() for i in [pp.aurect.x, pp.aurect.y]]
        return f"  {self.label} {self.aurect.x} {self.aurect.y} " + " ".join(map(str, flattencoords))

    @staticmethod
    def initcounter():
        """Staticmethod to reset the id generator"""
        EnemyBot._idcounter = count(0)

    def getmarkers(self):
        """Return all the Markers but the one equal to enemy initial position."""
        return self.pathmarkers.sprites()[:-1]

    def update(self, xoff, yoff):
        """Override method of base class to store also current offset and update the Markers rects"""
        self.off = [xoff, yoff]
        super(EnemyBot, self).update(xoff, yoff)
        for mrk in self.pathmarkers.sprites():
            mrk.update(xoff, yoff)

    def death_event(self):
        """Post a deathevent into the pygame.event queue"""
        newev = pygame.event.Event(src.DEATHEVENT)
        pygame.event.post(newev)

    def setspeed(self):
        """Set the x and y component of the velocity pointing to the next marker"""
        try:
            curmarkerrect = self.pathmarkers.sprites()[self._ipm].aurect
            self._ipm += 1
        except AttributeError:
            curmarkerrect = self.pathmarkers.sprites()[-1].aurect
            self._ipm = 0
            
        if self._ipm == len(self.pathmarkers.sprites()):
            self._ipm = 0

        self.nextrect = self.pathmarkers.sprites()[self._ipm].aurect
        
        vecdist = self.nextrect.distance(curmarkerrect)
        angle = np.arctan2(vecdist[1], vecdist[0])
        self.curspeed = np.array([self.speed*np.cos(angle), self.speed*np.sin(angle)])

    def movebot(self):
        """Move the bot by one frame time unit according to its velocity"""
        cvdist = self.nextrect.distance(self.aurect)
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
    """A fixed size block, The cursor controlled by the player.

    Children of Block. It's movement is controlled by the player through keyboard.
    Is affected by gravity, can move left, right and jump at fixed speed. Can climb ladders.
    There should be only one character in the maze.
    """
    
    rectsize = [20, 20]
    CURSORCOL = (255, 0, 0)
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3
    JUMP = 4
    resizable = False
  
    def __init__(self, pos):
        """Initialization:
        
        pos -- two-length list with x, y coordinates of top-left corner of the rectangle
        """
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
        """Override method of base class, adding custom informations"""
        return f"IP {self.aurect.x} {self.aurect.y}"

    def update(self, xoff, yoff):
        """Override method of base class to store also current offset"""
        self.off = [xoff, yoff]
        super(Character, self).update(xoff, yoff)
            
    def insidesurf(self, sface):
        """Check if the block is inside the surface 'sface'.

        Used to check if character is in the screen: if not, return the
        corresponding offset in order to draw the next part of the room.
        """
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
        """Check key pressed to set the motion direction"""
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
        """Set the force field. It's possible to set something different from just gravity.

        x, y are the acceleration components. If y is None, x must be a list holding both components.
        """
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
        """Apply the force field to get the velocity increment"""
        self.dvx += self.ax * src.TPF
        self.dvy += self.ay * src.TPF

    def movecharacter(self, groupwalls, groupladders):
        """Move the character in the room

        groupwalls -- a pygame.sprite.Group containing the Walls sprites.
        groupladders -- a pygame.sprite.Group containing the Ladder sprites.
        These two groups are used to check for collision and adjust the
        velocity. Then the block is moved by one frame time unit.
        """
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

