# mazegame
Simple platform game written in python. Choose a map, explore a series of rooms and look for the exit. A game editor allows to create custom maps.  
The game is _work in progress._

## Installation
The game require _python3.6_ or later, _numpy_, _lxml_ and _pygame_. _tkinter_ is used by the editor. Simply copy the files preserving the structure. Source files are in the _src_ directory, images are in the _images_ directory and maps are in the _gamemaps_ directory.

**mazegame.py** is the main script. Run it to play the game.

**mazeditor.py** is a game editor to create your custom maps

**testmap.py** is a testing script, useful to test the validity of a map. It makes use of _unittest_ to perform a set of validation checks on a map, searching for discrepancies in the file which could make the map invalid or unsolvable. The tester is not guaranteed to identify all possible problems, and a map may be still solvable if the test fails if designed with this intention.

## The game
The player controls a red square. It can move left or right, climb ladders up or down and jump. There are enemies which must be avoided (cannot be killed).  
Each map is divided into several rooms, connected by doors. Doors may be locked, in this case the player must collect the key to open the doors.
