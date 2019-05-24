#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  mazegame.py
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

"""Main script to start the game. To be used as an executable.

This file initialize the pygame library and loads the other
relevant files for the game.
"""


import sys
import os
import numpy as np
import pygame
from pygame import sprite
import pygame.locals as pyloc


import src.mzgmenu as mmenu
from src import PosManager

if __name__ == "__main__":
    #initializing stuffs
    pygame.init()
    screen = pygame.display.set_mode(PosManager.screen_size())
    pygame.display.set_caption("Mazegame")
    game = mmenu.TopLev(screen)
    game.gameloop()

#@@@ implement checkpoint blocks, and save/load game system
