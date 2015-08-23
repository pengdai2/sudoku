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
    The canonical ALS scenario involves a single restricted common
    hint (X) and one or more unrestricted common hints (Z) between
    the two ALS's. All instances of Z elsewhere that can see all the
    Z's within both ALS's can be eliminated.
    """
    def als_solo(self, plan, als1, als2, ucs, reason):
        status = False
        for hint in ucs:
            overlap = self.als_related(als1, hint) & self.als_related(als2, hint)
            if self.test_purge(overlap, set([hint])):
                self.purge_hints(plan, overlap, set([hint]), reason, "solo")
                status = True
        return status

    """
    A variation of the ALS scenario involves two restricted common
    hints between the two ALS's. This case is unlikely but possible
    and it leads to much more drastic actions. First, all hints
    within each ALS except for the two restricted common hints must
    be taken by the ALS. Hence, all instances of such hints elsewhere
    that can see all the instances of the same hint within the ALS
    can be eliminated. Secondly, the same rule applied in the solo
    case can be applied in the dual case with Z extended to include
    both unrestricted and restricted common hints.
    """
    def als_dual(self, plan, als1, als2, rcs, ucs, reason):
        status = False

        # Exclude any but the restricted common hints in each ALS.
        for als in (als1, als2):
            hints = self.als_all_hints(als) - rcs
            for hint in hints:
                nodes = self.als_related(als, hint)
                if self.test_purge(nodes, set([hint])):
                    self.purge_hints(plan, nodes, set([hint]), reason, "dual (excluded)")
                    status = True

        # Same solo rule except that we are not limited to just the
        # unrestricted common hints.
        for hint in rcs | ucs:
            overlap = self.als_related(als1, hint) & self.als_related(als2, hint)
            if self.test_purge(overlap, set([hint])):
                self.purge_hints(plan, overlap, set([hint]), reason, "dual (unrestricted)")
                status = True

        return status

    """
    Process the pair of ALS's.
    """
    def als(self, plan, als1, als2):
        # Get the restricted and unrestricted common hints.
        rcs, ucs = self.als_urc_hints(als1, als2)

        # ALS requires at least one restricted common hint.
        if not rcs:
            return False

        # Process the ALS pair differently depending on how many
        # restricted common hints there exist. Note that it is
        # impossible to have more than two restricted common hints
        # between two ALS's or we'd end up with more nodes than
        # there are hints.
        reason = {"als1": als1, "als2": als2, "rcs": rcs}

        if len(rcs) == 1:
            return self.als_solo(plan, als1, als2, ucs, reason)
        elif len(rcs) == 2:
            return self.als_dual(plan, als1, als2, rcs, ucs, reason)
        else:
            raise LogicException(reason)

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
