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

WindArea -- A block in which an external force acting on the character is present.

Checkpoint -- A checkpoint to save game.

Character -- The cursor controlled by the player.
"""

import os
import math
from itertools import count
from operator import itemgetter

import numpy as np
from lxml import etree

import pygame
from pygame import sprite
import pygame.locals as pyloc

import src
from src.mzgscreen import mazearea, editorarea

IMAGE_DIR = os.path.join(src.MAIN_DIR, '../images')


def add_counter(cls):
    """Decorator to add a counter to each class"""
    cls._idcounter = count(0)
    return cls


class Block(sprite.Sprite, src.PosManager):
    '''Common interface for all sprite block types.

    The methods are:
    fillimage -- fill the image with the bg color or mosaic tile
    update -- update pygame.Rect with the current position / size
    reprxml -- return text line of the block in map file format (used to create a map by the editor)
    reprxmlnew -- classmethod, used by editor to write lines of new blocks to be saved in the map file
    collidinggroup -- return other sprites of a group colliding with this sprite
    It has also the following property:
    risze -- get or set the size of the block, if resizable
    '''

    resizable = True
    actionmenu = {"Delete" : "delete", "Move to another room" : "move"}
    if src.ISGAME:
        area = mazearea
    else:
        area = editorarea

    def __init__(self, bid, pos, rsize, bg=None):
        """Initialization:

        bid -- sprite id
        pos -- two-length list with x, y coordinates of top-left corner of the rectangle
        rsize -- two-length list with width and height of the rectangle
        bg -- background color (3-length RGB tuple) or a pygame.Surface representing a tile
        """
        super(Block, self).__init__()
        self._id = bid
        self.image = pygame.Surface(self.sizetopix(rsize))
        self.aurect = src.FlRect(pos[0], pos[1], rsize[0], rsize[1])
        self.bg = bg
        Block.fillimage(self) #to avoid calling overriden versions

        #place block to its coordinates
        self.update(0, 0)

    @classmethod
    def recttopix(cls, rr, xoff=0, yoff=0):
        """Classmethod to use the correct recttopix method"""
        return cls.area.recttopix(rr, xoff, yoff)


    @classmethod
    def sizetopix(cls, rr):
        """Classmethod to use the correct sizetopix method"""
        return cls.area.sizetopix(rr)


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
        self.rect = self.recttopix(self.aurect, xoff, yoff)

    @property
    def rsize(self):
        return [self.aurect.width, self.aurect.height]

    @rsize.setter
    def rsize(self, newsize):
        if self.resizable:
            nwpxsize = self.sizetopix(newsize)
            if any([i <= 2 for i in nwpxsize]):
                return
            self.aurect.width = newsize[0]
            self.aurect.height = newsize[1]
            self.image = pygame.transform.scale(self.image, nwpxsize)
            self.fillimage()

    def reprxml(self):
        """Return etree Element of the current block (used by the editor)

        This is a basic tag providing attributes as defined in the schema, child classes need to override this method
        to add other attributes if needed.
        """
        return etree.Element(self.__class__.__name__, blockid=str(self._id),
                             x=str(self.aurect.x), y=str(self.aurect.y))

    @classmethod
    def reprxmlnew(cls, **kwargs):
        """Return default xml tag for a new block in map file format (used by the editor)

        Classmethod. idepos is a 3-length list containing the id and x y coordinates
        *kwargs is a dictionary containing the attributes of the xml Element tag, and vary from block type
        to block type. Mandatory attributes must be blockid, x, y.
        Block types in need of a tag with nested tags need to override this method.
        """
        if cls.__name__ == "Block":
            raise RuntimeError("reprxmlnew classmethod should not be called by a Block instance!")

        try:
            out = itemgetter('blockid', 'x', 'y')(kwargs)
        except KeyError as e:
            raise RuntimeError("Missing parameter(s) given to reprxlmnew!\n" + str(e))

        res = etree.Element(cls.__name__, **kwargs)
        if not hasattr(cls, "rectsize"):
            #assigning initial width and height
            res.set("width", "100")
            res.set("height", "50")

        return res

    def collidinggroup(self, group):
        """Return other sprites of a group colliding with this sprite"""
        return [sp for sp in group.sprites() if self.aurect.colliderect(sp.aurect)]

    @classmethod
    def initcounter(cls):
        """Classmethod to reset the id generator"""
        cls._idcounter = count(0)

    def blitinfo(self, *args):
        text = '.'.join(map(str, args))
        mfont = pygame.font.Font(None, 30)
        surftext = mfont.render(text, True, (255, 0, 0))
        self.image.blit(surftext, (0, 0))


@add_counter
class Marker(Block):
    """An invisible, any size but not resizable block, used to mark a position on the screen.

    Children of Block. Markers have an id incremented by 1 each time a new Marker
    is created, but can be resetted by the initcounter method.
    """
    
    resizable = False
    label = 'M'
    BGCOL = (100, 100, 100)
    
    def __init__(self, bid, pos, rsize, ref):
        """Initialization:
        
        bid -- sprite id
        pos -- two-length list with x, y coordinates of top-left corner of the rectangle
        rsize -- two-length list with width and height of the rectangle
        ref -- reference to another Block which uses this Marker
        by the game or by the editor.
        """
        self.ref = ref
        if src.ISGAME:
            bg = None
        else:
            bg = self.BGCOL
        super(Marker, self).__init__(bid, pos, rsize, bg)
        self.fillimage()
        
    def fillimage(self):
        super(Marker, self).fillimage()
        if not src.ISGAME:
            self.blitinfo(self.ref, self._id)

    #no need to override reprxml method for marker


@add_counter
class Wall(Block):
    """A solid wall of any size, can be used as floor, roof, or vertical wall.

    Children of Block.
    """
    
    label = 'W'
    BGCOL = (255, 255, 255)
    
    def __init__(self, bid, pos, rsize):
        """Initialization:
        
        bid -- sprite id
        pos -- two-length list with x, y coordinates of top-left corner of the rectangle
        rsize -- two-length list with width and height of the rectangle
        """
        super(Wall, self).__init__(bid, pos, rsize, self.BGCOL)

    def reprxml(self):
        """Override method of base class, adding extra attributes"""
        el = super(Wall, self).reprxml()
        el.set("width", str(self.aurect.width))
        el.set("height", str(self.aurect.height))
        return el


@add_counter
class Ladder(Block):
    """A ladder can be of any size. Can be crossed and climbed to reach high platforms.

    Children of Block.
    """
    
    label = 'L'
    BGIMAGE = pygame.image.load(os.path.join(IMAGE_DIR, "ladderpattern.png"))

    def __init__(self, bid, pos, rsize):
        """Initialization:
        
        bid -- sprite id
        pos -- two-length list with x, y coordinates of top-left corner of the rectangle
        rsize -- two-length list with width and height of the rectangle
        """
        super(Ladder, self).__init__(bid, pos, rsize, self.BGIMAGE)

    def reprxml(self):
        """Override method of base class, adding extra attributes"""
        el = super(Ladder, self).reprxml()
        el.set("width", str(self.aurect.width))
        el.set("height", str(self.aurect.height))
        return el


@add_counter
class DeadlyBlock(Block):
    """A block (any size) which should not be touched. Is game over.

    Children of Block. Create a death event if the player collides with it.
    """

    label = 'T'
    BGCOL = (0, 0, 255)

    def __init__(self, bid, pos, rsize):
        """Initialization:
        
        bid -- sprite id
        pos -- two-length list with x, y coordinates of top-left corner of the rectangle
        rsize -- two-length list with width and height of the rectangle
        """
        super(DeadlyBlock, self).__init__(bid, pos, rsize, self.BGCOL)

    def death_event(self):
        """Post a deathevent into the pygame.event queue"""
        newev = pygame.event.Event(src.DEATHEVENT)
        pygame.event.post(newev)

    def reprxml(self):
        """Override method of base class, adding extra attributes"""
        el = super(DeadlyBlock, self).reprxml()
        el.set("width", str(self.aurect.width))
        el.set("height", str(self.aurect.height))
        return el


@add_counter
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
    rectsize = [50, 50]
    label = 'D'
    LDOOR = pygame.image.load(os.path.join(IMAGE_DIR, "lockeddoor.png"))
    LOCKEDDOOR = pygame.transform.scale(LDOOR, Block.sizetopix(rectsize))
    ODOOR = pygame.image.load(os.path.join(IMAGE_DIR, "opendoor.png"))
    OPENDOOR = pygame.transform.scale(ODOOR, Block.sizetopix(rectsize))
    LEXIT = pygame.image.load(os.path.join(IMAGE_DIR, "lockedexit.png"))
    LOCKEDEXIT = pygame.transform.scale(LEXIT, Block.sizetopix(rectsize))
    OEXIT = pygame.image.load(os.path.join(IMAGE_DIR, "openexit.png"))
    OPENEXIT = pygame.transform.scale(OEXIT, Block.sizetopix(rectsize))

    def __init__(self, bid, pos, doorid, lock):
        """Initialization:

        bid -- sprite id
        pos -- two-length list with x, y coordinates of top-left corner of the rectangle
        doorid -- the id of the other end of the passage (the destination door).
        lock -- boolean or anythin that can be casted to boolean. If true the door is locked.
        """
        super(Door, self).__init__(bid, pos, self.rectsize)
        self.destination = doorid
        self.locked = bool(lock)
        self.fillimage()
        
    def fillimage(self):
        super(Door, self).fillimage()
        if not src.ISGAME:
            self.blitinfo(self._id, self.destination)

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

    def reprxml(self):
        """Override method of base class, adding extra attributes"""
        el = super(Door, self).reprxml()
        ilock = "true" if self.locked else "false"
        el.set("destination", str(self.destination))
        el.set("locked", ilock)
        return el


@add_counter
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
    rectsize = [50, 50]
    label = 'K'
    RAWIMKEY = pygame.image.load(os.path.join(IMAGE_DIR, "key.png"))
    IMKEY = pygame.transform.scale(RAWIMKEY, Block.area.sizetopix(rectsize))

    def __init__(self, bid, pos, dooridlist):
        """Initialization:

        bid -- sprite id
        pos -- two-length list with x, y coordinates of top-left corner of the rectangle
        dooridlist --  a list of the door ids which the key opens.
        """
        super(Key, self).__init__(bid, pos, self.rectsize)
        self.whoopen = dooridlist
        self.taken = False
        self.fillimage()

    def fillimage(self):
        super(Key, self).fillimage()
        if not src.ISGAME:
            self.blitinfo(*self.whoopen)

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

    def reprxml(self):
        """Override method of base class, adding extra attributes"""
        el = super(Key, self).reprxml()
        el.set("keyid", ";".join(map(str, self.whoopen)))
        return el


@add_counter
class EnemyBot(Block):
    """A fixed size block, it represents a enemy moving on a prefixed path. 

    Children of Block. A EnemyBot has a numeric id and moves at fixed speed in the room.
    Markers are used to determine the path: the bot moves from one marker to the next
    in a straight line, returns at the starting point and restart in a loop.
    If the player touches them, it's game over.
    """

    resizable = False
    rectsize = [30, 30]
    label = 'B'
    BGCOL = (0, 255, 0)
    speed = 150
    actionmenu = dict(Block.actionmenu)
    actionmenu["Add Marker"] = "addmarker"

    def __init__(self, bid, pos, *coordlist):
        """Initialization:
        
        bid -- sprite id
        pos -- two-length list with x, y coordinates of top-left corner of the rectangle
        *coordlist -- variadic, flat list of x y coordinates, used to create the Markers. Each pair
        represent the top left corner of the Marker rectangle.
        """
        super(EnemyBot, self).__init__(bid, pos, self.rectsize, self.BGCOL)
        Marker.initcounter()
        coordpoints = [crd for crd in src.pairextractor(*coordlist)] + [pos]
        self.pathmarkers = sprite.Group([Marker(next(Marker._idcounter), cppos, self.rectsize, self._id) for cppos in coordpoints]) #id of markers
        self.setspeed()
        self.fillimage()
        
    def fillimage(self):
        super(EnemyBot, self).fillimage()
        if not src.ISGAME:
            self.blitinfo(self._id)

    def reprxml(self):
        """Override method of base class, adding required subelements"""
        el = super(EnemyBot, self).reprxml()
        for mrk in self.getmarkers():
            el.append(mrk.reprxml())
        return el

    @classmethod
    def reprxmlnew(cls, **kwargs):
        """Return xml tag for a new EnemyBot"""
        fund_kwargs = {k: kwargs[k] for k in ("blockid", "x", "y")}
        res = super(EnemyBot, cls).reprxmlnew(**fund_kwargs)
        mrkx = int(kwargs["x"])
        mrky = kwargs["y"]
        for i in range(1, kwargs["nummarker"]+1):
            mrid = next(Marker._idcounter)
            mrkattr = {"blockid":str(mrid), "x":str(mrkx + i*50), "y":mrky}
            res.append(Marker.reprxmlnew(**mrkattr))
        return res

    def getmarkers(self):
        """Return all the Markers but the one equal to enemy initial position"""
        return self.pathmarkers.sprites()[:-1]

    def addmarker(self, x, y):
        """Add a marker to pathmakers group, used by editor."""
        last = self.pathmarkers.sprites()[-1]
        self.pathmarkers.remove(last)
        self.pathmarkers.add(Marker(last._id, [x, y], self.rectsize, self._id, False))
        last._id += 1
        self.pathmarkers.add(last)
        
    def update(self, xoff, yoff):
        """Override method of base class to store also current offset and update the Markers rects"""
        self.off = [xoff, yoff]
        super(EnemyBot, self).update(xoff, yoff)
        try:
            for mrk in self.pathmarkers.sprites():
                mrk.update(xoff, yoff)
        except AttributeError:
            pass

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
            self.rect = self.recttopix(self.aurect, self.off[0], self.off[1])
        else:
            self.aurect.x = self.pathmarkers.sprites()[self._ipm].aurect.x
            self.aurect.y = self.pathmarkers.sprites()[self._ipm].aurect.y
            self.setspeed()


@add_counter
class WindArea(Block):
    """A surface with an additional force field.

    Children of Block. Can be visible or invisible, the force of the wind
    may have different intensities.
    """

    label = 'F'
    WINDUP = pygame.image.load(os.path.join(IMAGE_DIR, "windarrow.png"))
    WINDUPRI = pygame.image.load(os.path.join(IMAGE_DIR, "windarrowdiag.png"))
    WINDLE = pygame.transform.rotate(WINDUP, 90)
    WINDDO = pygame.transform.rotate(WINDUP, 180)
    WINDRI = pygame.transform.rotate(WINDUP, 270)
    WINDUPLE = pygame.transform.rotate(WINDUPRI, 90)
    WINDDOLE = pygame.transform.rotate(WINDUPRI, 180)
    WINDDORI = pygame.transform.rotate(WINDUPRI, 270)
    _winddict = {0 : [np.array([0.0, -1.0]), WINDUP], 1 : [np.array([1.0, -1.0]), WINDUPRI], 2 : [np.array([1.0, 0.0]), WINDRI],
                3 : [np.array([1.0, 1.0]), WINDDORI], 4 : [np.array([0.0, 1.0]), WINDDO], 5 : [np.array([-1.0, 1.0]), WINDDOLE],
                6 : [np.array([-1.0, 0.0]), WINDLE], 7 : [np.array([-1.0, -1.0]), WINDUPLE]}
    _forcefactor = 100.0
    cursorinside = None

    actionmenu = dict(Block.actionmenu)
    actionmenu["Edit wind"] = "editwind"

    def __init__(self, bid, pos, rsize, windpar, vis=True):
        """Inizializaton:

        bid -- sprite id
        pos -- two-length list with x, y coordinates of top-left corner of the rectangle
        rsize -- two-length list with width and height of the rectangle
        windpar -- two-length list containing two integers: the first from 0 to 7 indicates the wind direction
        the second indicates the strength of the wind. Actual wind force is this integer times 100
        vis -- boolean, in False windarea is invisible"""
        super(WindArea, self).__init__(bid, pos, rsize)
        self._windpar = windpar
        try:
            self.wind = self._winddict[self._windpar[0]][0] * self._windpar[1] * self._forcefactor
        except KeyError as e:
            raise Exception('Error in instantiating WindArea, direction should be an integer between 0 and 7') from e
        self.visible = vis

    def fillimage(self):
        """Override"""
        if self._visible:
            self.bg = self._winddict[self._windpar[0]][1]
            super(WindArea, self).fillimage()
        else:
            self.bg = None
            self.image.fill((0, 0, 0))
        if not src.ISGAME:
            pygame.draw.rect(self.image, (100, 0, 0), self.image.get_rect(), 10)
            self.blitinfo(*self._windpar)
            
    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, boolvalue):
        self._visible = boolvalue
        self.fillimage()

    def entering_wind_event(self):
        """Post the entering wind event to the pygame.event system"""
        newev = pygame.event.Event(src.ENTERINGEVENT, wind=self.wind)
        pygame.event.post(newev)

    def exiting_wind_event(self):
        """Post the exiting wind event to the pygame.event system"""
        newev = pygame.event.Event(src.EXITINGEVENT, wind=np.array([0, 0]))
        pygame.event.post(newev)

    def reprxml(self):
        """Override method of base class, adding extra attributes"""
        el = super(WindArea, self).reprxml()
        ivis = "true" if self.visible else "false"
        el.set("width", str(self.aurect.width))
        el.set("height", str(self.aurect.height))
        el.set("compass-direction", str(self._windpar[0]))
        el.set("strength", str(self._windpar[1]))
        el.set("visible", ivis)
        return el


@add_counter
class Checkpoint(Block):
    """A fixed size area which allows to save the game on entering.

    Children of block.
    """

    resizable = False
    rectsize = [50, 50]
    label = 'C'
    RAWIMCP = pygame.image.load(os.path.join(IMAGE_DIR, "checkpoint.png"))
    IMCP = pygame.transform.scale(RAWIMCP, Block.area.sizetopix(rectsize))
    
    def __init__(self, bid, pos):
        super(Checkpoint, self).__init__(bid, pos, self.rectsize, self.IMCP)
 
    #no need to override reprxml method for checkpoint

    def checkp_event(self):
        """Post a checkpevent into the pygame.event queue"""
        newev = pygame.event.Event(src.CHECKPEVENT, key_id=self._id)
        pygame.event.post(newev)


class Character(Block):
    """A fixed size block, the cursor controlled by the player.

    Children of Block. It's movement is controlled by the player through keyboard.
    Is affected by gravity, can move left, right and jump at fixed speed. Can climb ladders.
    There should be only one character in the maze.
    """
    
    resizable = False
    rectsize = [20, 20]
    CURSORCOL = (255, 0, 0)
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3
    JUMP = 4
    
    def __init__(self, pos, iniroom):
        """Initialization:
        
        pos -- two-length list with x, y coordinates of top-left corner of the rectangle
        iniroom -- id of initial room
        """
        super(Character, self).__init__(0, pos, self.rectsize, self.CURSORCOL)
        self.current_direction = set()
        self.cridx = iniroom
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

    def reprxml(self):
        """Override method of base class, adding extra attributes"""
        el = super(Character, self).reprxml()
        el.set("initialroom", str(self.cridx))
        return el

    @classmethod
    def reprxmlnew(cls, **kwargs):
        """Override method to raise error, Character object must not call this"""
        raise NotImplementedError("Character do not need to be created by the editor")

    def update(self, xoff, yoff):
        """Override method of base class to store also current offset"""
        self.off = np.array([xoff, yoff])
        super(Character, self).update(xoff, yoff)
            
    def insidearea(self):
        """Check if the character is inside the shown area of the room.

        Returns None if is inside, otherwise returns the corresponding
        offset in order to draw the next part of the room.
        """
        coff = self.off * 1000
        cnt = src.FlRect(coff[0], coff[1], coff[0]+1000, coff[1]+1000)
        if cnt.contains(self.aurect):
            return None
        else:
            if self.aurect.centery < cnt.top:
                return np.array([0, -1])
            elif self.aurect.centerx < cnt.left:
                return np.array([-1, 0])
            elif self.aurect.centery > cnt.bottom:
                return np.array([0, 1])
            elif self.aurect.centerx > cnt.right:
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
            if isinstance(x, (tuple, list, np.ndarray)):
                self.ax = x[0]
                self.ay = x[1]
            else:
                raise RuntimeError("Wrong initialization parameter.")
        else:
            self.ax = x
            self.ay = y

    def applyforce(self):
        """Apply the force field to get the velocity increment"""
        self.dvx += (self.ax - 0.5*self.dvx) * src.TPF
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
            self.dvx = 0
            self.dvy = 0

        self.current_direction.clear()
        self.rect = self.recttopix(self.aurect, self.off[0], self.off[1])
