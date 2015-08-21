#
# Trial based strategy module
#

from logger import *
from playbook import *
from sudoku import *

class Trial(Strategy):

    def __init__(self, name):
        Strategy.__init__(self, name)

    def try_hints(self, plan, hints):
        sudoku = plan.get_sudoku()
        trial = sudoku.snap()

        # Take a leap of faith with the given hints and then run deduction
        self.debug(2, "hints {0}".format(hints))

        for hint in hints:
            node, value = hint
            copy = trial.get_node(node.get_row().get_ident(), node.get_col().get_ident())
            copy.set_value(value)

        # Disable high level strategies for trial runs.
        options = plan.get_options().copy()
        for strategy in Playbook.all_strategies():
            if options.get_level(strategy) > 1:
                options.disable(strategy)

        if Playbook.solve(trial, options, True):
            sudoku.copy(trial)
            return True

        return False

class TrialOne(Trial):

    __metaclass__ = StrategyMeta

    def __init__(self):
        Trial.__init__(self, "TRIAL-1")

    """
    For each incomplete node, try each hint by brute force.
    For each iteration, there are 3 different outcomes:
    
      1) success - hit the jack pot
      2) impasse - wasted work, try next
      3) invalid - eliminate the hint
      
    For case 3, we will have a winner if all but the last hint is
    eliminated, in which case, abort the current round of guessing
    and start over.
    """
    def run(self, plan):
        sudoku = plan.get_sudoku()
        for node in sudoku.get_incomplete():
            for hint in node.get_hints():
                hints = ((node, hint), )
                try:
                    if self.try_hints(plan, hints):
                        return True
                except LogicException:
                    # Wrong guess. Eliminate the hint.
                    self.purge_hints(plan, [node], set([hint]))
                    if node.is_complete():
                        return True
        return False

class TrialTwo(Trial):

    __metaclass__ = StrategyMeta

    def __init__(self):
        Trial.__init__(self, "TRIAL-2")

    """
    Similar to TrialOne except we make two guesses on different nodes.
    We can eliminate the hint on the first node if all hints on the
    remainning nodes lead to invalid. Few but known sudoku instances
    require this strategy.
    """
    def run(self, plan):
        sudoku = plan.get_sudoku()
        for node in sudoku.get_incomplete():
            for hint in node.get_hints():
                invalid = True
                for node2 in sudoku.get_incomplete():
                    if node2 == node:
                        continue
                    for hint2 in node2.get_hints():
                        hints = ((node, hint), (node2, hint2))
                        try:
                            if self.try_hints(plan, hints):
                                return True
                            invalid = False
                        except LogicException:
                            continue
                if invalid:
                    self.purge_hints(plan, [node], set([hint]))
                    if node.is_complete():
                        return True
        return False

class TrialThree(Trial):

    __metaclass__ = StrategyMeta

    def __init__(self):
        Trial.__init__(self, "TRIAL-3")

    """
    Similar to TrialOne except the search now include three guesses.
    This is purely academic as no known sudoku instances are found
    to require this strategy.
    """
    def run(self, plan):
        sudoku = plan.get_sudoku()
        for node in sudoku.get_incomplete():
            for hint in node.get_hints():
                invalid = True
                for node2 in sudoku.get_incomplete():
                    if node2 == node:
                        continue
                    for hint2 in node2.get_hints():
                        for node3 in sudoku.get_incomplete():
                            if node3 == node or node3 == node2:
                                continue
                            for hint3 in node3.get_hints():
                                hints = ((node, hint), (node2, hint2), (node3, hint3))
                                try:
                                    if self.try_hints(plan, hints):
                                        return True
                                    invalid = False
                                except LogicException:
                                    continue
                if invalid:
                    self.purge_hints(plan, [node], set([hint]))
                    if node.is_complete():
                        return True
        return False
