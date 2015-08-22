#
# WXYZ-Wing strategy module
#

import itertools
from logger import *
from playbook import *
from sudoku import *
from almost_locked_set import *

class WXYZWing(AlmostLockedSet):

    __metaclass__ = StrategyMeta

    """
    WXYZ-WING can be considered as a group of 4 nodes and 4 hints,
    that has exactly one non-restricted common hint. We use that
    hint (Z) to eliminate since at least one of Z will be the solution.

    WXYZ-WING consists of a hinge, or the subset of nodes that can see
    all other nodes. If the hinge contains Z, Z may be eliminated from
    an area visible to all nodes in the WXYZ-WING. Otherwise, the area
    expands to one that is visible to all nodes but the hinge.

    WXYZ-WING is actually a special case of ALS, where the wing is made
    up of a 1-node and a 3-node ALS, respectively. The two ALS's share
    a restricted common hint, W, and a unrestricted common hint, Z. As
    such, the total number of hints remains 4 across the two ALS's.
    """
    def __init__(self):
        AlmostLockedSet.__init__(self, "WXYZ-WING")

    """
    Validate the WXYZ-WING pattern and process it if found.
    """
    def wxyz_wing(self, plan, als1, als3):
        rcs, ucs = self.als_urc_hints(als1, als3)
        if len(ucs) != 1 or len(rcs) != 1:
            return False

        hinge = self.als_hinge(als1, als3)
        wing = (als1 | als3) - hinge
        reason = {"hint": ucs, "hinge": hinge, "wing": wing}

        hint = ucs.pop()
        ucs.add(hint)
        overlap = self.als_related(als1, hint) & self.als_related(als3, hint)
        if self.test_purge(overlap, set(ucs)):
            self.purge_hints(plan, overlap, set(ucs), reason)
            return True

        return False

    """
    WXYZ-WING strategy.
    """
    def run(self, plan):
        status = False
        alsets1 = self.als_find_in_nodes(plan.get_sudoku().get_incomplete(), [1])
        alsets3 = self.als_find_in_lots(plan.get_sudoku().get_lots(), [3])
        for als1 in alsets1:
            if any([x.is_complete() for x in als1]):
                continue
            for als3 in alsets3:
                if any([x.is_complete() for x in als3]):
                    continue
                if self.wxyz_wing(plan, als1, als3):
                    status = True
        return status
