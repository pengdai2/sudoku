#
# Sudoku logger module
#
# This module provides a simple logger implementation.
#

class Logger(object):

    debug_level = 3

    @staticmethod
    def debug(level, message):
        if level <= Logger.debug_level:
            print ">>DEBUG{0}: {1}".format(level, message)
