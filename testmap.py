#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  testmap.py
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

import unittest

import sys
import os
import readline
import pygame
from pygame import sprite
from pygame.locals import *

import src
from src.mzgrooms import *

#if pygame display is not initialized, images cannot be converted and Block building fails.
pygame.display.set_mode(src.PosManager.screen_size())


class TestMaze(unittest.TestCase):
    game = None

    def getdoorlist(self):
        doorlist = []
        for rr in self.game.rooms:
            doorlist.extend(rr.doors.sprites())
        return doorlist

    def getkeylist(self):
        keylist = []
        for rr in self.game.rooms:
            keylist.extend(rr.keys.sprites())
        return keylist

    def test_inipos(self):
        try:
            self.game.croom.screenfrac(self.game.cursor)
        except RuntimeError:
            ermess = "character initial position is outside the room!"
            self.fail(ermess)

    def test_blocksoverlapping(self):
        for rr in self.game.rooms:
            albl = rr.allblocks.sprites()
            if self.game.firstroom == rr.roompos:
                albl.append(self.game.cursor)
            for i, bl in enumerate(albl[:-1]):
                for obl in albl[i+1:]:
                    txtmess = f"overlap!\n{bl.reprline()}\n{obl.reprline()}"
                    self.assertFalse(bl.aurect.colliderect(obl.aurect), txtmess)
    
    def test_doors(self):
        doorlist = self.getdoorlist()
        for door in doorlist:
            if door.destination >= 0:
                cmessa = f"door id {door._id} should not lead to itself!"
                self.assertFalse(door._id == door.destination, cmessa)
                targetdoor = [(dd._id, dd.destination, dd.locked) for dd in doorlist if dd._id == door.destination and dd.destination == door._id]

                cmessb = f"door id: {door._id} leading to multiple doors!"
                self.assertTrue(len(targetdoor) == 1, cmessb)

                cmessc = f"door id: {door._id} leading to door {door.destination} is not corresponded!"
                self.assertTrue((door.destination, door._id) == (targetdoor[0][0], targetdoor[0][1]), cmessc)
                
                cmessd = f"door ids: {door._id} and {door.destination} are corresponded, but one is locked and the other not!"
                self.assertTrue(door.locked == targetdoor[0][2], cmessd)

    def test_keys(self):
        doorlist = self.getdoorlist()
        keylist = self.getkeylist()

        for door in doorlist:
            if door.locked:
                cmessa = f"door id {door._id} is locked but there is no key for it!"
                self.assertTrue(door._id in [idk for key in keylist for idk in key.whoopen], cmessa)

        for key in keylist:
            cmessb = f"key id {key._id} does not open any door!"
            self.assertFalse(len(key.whoopen) == 0, cmessb)

            if len(key.whoopen) == 2:
                doors = [dd for dd in doorlist if dd._id in key.whoopen]
                cmessc = f"key id {key._id} opens two not corresponding doors {doors[0]._id} and {doors[1]._id}!"
                self.assertTrue(doors[0]._id == doors[1].destination and doors[1]._id == doors[0].destination, cmessc)

            cmessd = f"key id {key._id} opens more than two doors!"
            self.assertFalse(len(key.whoopen) > 2, cmessd)


if __name__ == '__main__':
    MDIR = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
    docpath = os.path.join(MDIR, "gamemaps")
    print("Testing the correctness of a file game.")
    os.chdir(docpath)
    readline.parse_and_bind('tab: complete')

    filegame = input("Type a game filename: ")
    TestMaze.game = Maze(filegame)
    os.chdir(MDIR)

    unittest.main()
