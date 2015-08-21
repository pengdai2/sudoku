#!/usr/bin/python
#
# Sudoku game module.
#
# This module defines the main game intance. It is responsible for
# interacting with the user, loading sudoku instances from file,
# and calling upon the playbook for solutions.
#

import re
import sys
from logger import *
from sudoku import *
from playbook import *
from strategy import *
from hook import *

class Game(object):

    verbose = False

    @staticmethod
    def usage():
        print "Usage: sudoku filename [id]"

    @staticmethod
    def solve(ident):
        sudoku = Game.get_instance(ident)
        if not sudoku:
            print "Invalid sudoku instance!"
            return

        print "Sudoku instance:", ident
        if Game.verbose:
            print sudoku.format(verbose = True)
        else:
            print sudoku.format(pretty = True)

        if Playbook.solve(sudoku):
            print "Answer:"
        else:
            print "Sorry. It's too hard!"
        if Game.verbose:
            print sudoku.format(verbose = True)
        else:
            print sudoku.format(pretty = True)

    @staticmethod
    def run():
        argc = len(sys.argv)
        if argc < 2 or argc > 3:
            Game.usage()
            return

        if argc == 3:
            Game.solve(sys.argv[2])
            return

        while True:
            ident = raw_input("Enter the sudoku instance: ")
            if ident == "done":
                print "Bon Voyage!"
                break
            Game.solve(ident)

    @staticmethod
    def get_instance(ident):
        fhandle = open(sys.argv[1])
        if not Game.find_grid(fhandle, ident):
            return None
        grid = Game.read_grid(fhandle)
        sudoku = Sudoku.load(grid, ident)
        return sudoku

    # 
    # Find the n-th grid in the file. Return True if found and False
    # otherwise. The file is positioned at the beginning of the grid
    # found.
    # 
    @staticmethod
    def find_grid(fhandle, ident):
        for line in fhandle:
            if line.startswith("Grid"):
                if ident == line.split()[1]:
                    return True
        return False

    # 
    # Read the 9x9 grid which consists of 9 lines each of which has
    # 9 digits from 0 to 9.
    # 
    @staticmethod
    def read_grid(fhandle):
        text = ""
        pattern = re.compile("^\d|\[[1-9](?:\s*,\s*[1-9]){1,8}\]")
        for line in fhandle:
            line = line.strip()
            if not pattern.match(line):
                break
            text = text + line
        return text

# Rock it, baby!
Game.run()
