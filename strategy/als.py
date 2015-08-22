#
# Almost Locked Set (ALS) strategy module
#

import itertools
from logger import *
from playbook import *
from sudoku import *
from almost_locked_set import *

class ALS(AlmostLockedSet):

    __metaclass__ = StrategyMeta

    """
    For this strategy to work, it requires two ALS's that can "see"
    each other. Specifically, there must exist a restricted common
    hint (X) and a non-restricted common hint (Z) between the two
    ALS's.

    The strategy eliminates all occurrences of hint Z outside of the
    two ALS's but can see all instances of Z in both ALS's.

    Y-WING, XYZ-WING, and WXYZ-WING are all special cases of the ALS
    strategy. For example, in the case of XYZ-WING, the node YZ is a
    2-value ALS by itself; and the pair XYZ and XZ form another ALS.
    Y is the restricted common hint whereas Z is the unrestricted.
    """
    def __init__(self):
        AlmostLockedSet.__init__(self, "ALS")

    """
    Process the pair of ALS's.
    """
    def als(self, plan, als1, als2):
        status = False

        # Make sure there exists at least one restricted common hint.
        rcs, ucs = self.als_urc_hints(als1, als2)
        if not rcs:
            return status

        # Remove conflicting instances of any non-restricted
        # common hints.
        reason = {"als1": als1, "als2": als2, "rcs": rcs}
        for hint in ucs:
            overlap = self.als_related(als1, hint) & self.als_related(als2, hint)
            if self.test_purge(overlap, set([hint])):
                self.purge_hints(plan, overlap, set([hint]), reason)
                status = True

        return status

    """
    ALS strategy.
    """
    def run(self, plan):
        status = False
        alsets = self.als_find_in_lots(plan.get_sudoku().get_lots())
        for als1, als2 in itertools.combinations(alsets, 2):
            if any([x.is_complete() for x in als1 | als2]):
                continue
            if als1 & als2:
                continue
            if self.als(plan, als1, als2):
                status = True
        return status
