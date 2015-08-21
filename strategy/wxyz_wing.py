#
# WXYZ-Wing strategy module
#

import itertools
from logger import *
from playbook import *
from sudoku import *

class WXYZWing(Strategy):

    __metaclass__ = StrategyMeta

    """
    WXYZ-WING can be considered as a group of 4 nodes and 4 hints,
    that has exactly one non-restricted common hint. We use that
    hint (Z) to eliminate since at least one of Z will be the solution.
    A restricted hint N, is one where all the instances of it in the
    pattern can see each other; vice versa for non-restricted hint.
    WXYZ-WING consists of a hinge, or the subset of nodes that can see
    all nodes in the pattern. If the hinge contains Z, Z may be eliminated
    from an area visible to all nodes in the WXYZ-WING. Otherwise, the area
    expands to one that is visible to all nodes but the hinges.
    """
    def __init__(self):
        Strategy.__init__(self, "WXYZ-WING")

    """
    Validate the WXYZ-WING pattern and process it if found.
    """
    def wxyz_wing(self, plan, wing):
        hints = set.union(*[x.get_hints() for x in wing])
        if len(hints) != 4:
            return False

        # Count restricted and non-restricted hints in the pattern.
        connected = 0
        for hint in hints:
            nodes = [node for node in wing if node.has_hint(hint)]
            lots = set.intersection(*[set(x.get_lots()) for x in nodes])
            if lots:
                connected += 1
            else:
                z = hint
        if connected != 3:
            return False

        # Hinges are nodes that can see all other nodes in the pattern.
        # The rest of the nodes in the pattern are referred to as wing.
        hinges = [x for x in wing if all([x.is_related(y) for y in wing])]
        if not hinges:
            return False

        # Where to eliminate Z depends on whether the hinges contain Z.
        # If the hinges don't have Z, the target area includes those all
        # nodes in the pattern except the hinges can see. This is similar
        # to (X)Y-Wing and XYZ-Wing.
        if any([x.has_hint(z) for x in hinges]):
            overlap = self.join_related(wing)
        else:
            overlap = self.join_related(set(wing) - set(hinges))

        hints = set([z])
        if self.test_purge(overlap, hints):
            reason = {"hint": sorted(hints), "hinges": hinges,
                      "wing": list(set(wing) - set(hinges))}
            self.purge_hints(plan, overlap, hints, reason)
            return True

        return False

    """
    WXYZ-WING strategy.
    """
    def run(self, plan):
        status = False
        for wing in itertools.combinations(plan.get_sudoku().get_incomplete(), 4):
            if any([x.is_complete() for x in wing]):
                continue
            if self.wxyz_wing(plan, wing):
                status = True
        return status
