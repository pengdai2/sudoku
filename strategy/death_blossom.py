#
# Death Blossom strategy module
#

import itertools
from logger import *
from playbook import *
from sudoku import *
from almost_locked_set import *

class DeathBlossom(AlmostLockedSet):

    __metaclass__ = StrategyMeta

    """
    Death Blossom is another variation of the Almost Locked Set based
    strategies. For this strategy to work, it requires three ALS's, A,
    B, and C, that can "see" each other. Specifically, there must exist
    a restricted common hint (X) between A and B; and one (Y) between
    A and C; and an unrestricted common hint (Z) between B and C.

    The strategy eliminates all occurrences of hint Z outside of the
    two ALS's, B and C, but can see all instances of Z in both ALS's.

    It differs from ALS in that the two ALS's, B and C, are not directly
    linked to each other. Instead, they are linked via the "stem" ALS A
    with B and C forming petals around it. Hence, the name Death Blossom.

    In a way, it is analagous to XY-WING, where node XY is the stem and
    node XZ and YZ are the petals, except that the parts that make Death
    Blossom are ALS's not nodes.

    Given the third dimension, Death Blossom can be orders of magnitude
    more expensive than plain ALS. Hence, an artificial limit on the
    size of the stem is put in place to cap the cost.
    """
    def __init__(self, stem_limit = 1):
        AlmostLockedSet.__init__(self, "DEATH-BLOSSOM")
        self.stem_limit = stem_limit

    """
    Find the stem in the Death Blossom.
    """
    def death_blossom_stem(self, alsets):
        for stem in alsets:
            if len(stem) > self.stem_limit:
                continue
            petal1, petal2 = list(alsets - set([stem]))
            x, ucs = self.als_urc_hints(petal1, petal2)
            if x or not ucs:
                continue
            rcs1, x = self.als_urc_hints(stem, petal1)
            rcs2, x = self.als_urc_hints(stem, petal2)
            if not rcs1 or not rcs2:
                continue
            rcs = rcs1 | rcs2
            if len(rcs) < 2:
                continue
            ucs -= rcs
            return (stem, rcs, ucs)
        return (None, None, None)

    """
    Verify and process the death blossom pattern.
    """
    def death_blossom(self, plan, alsets):
        status = False

        stem, rcs, ucs = self.death_blossom_stem(alsets)
        if not stem:
            return status
        alsets.remove(stem)
        petal1 = alsets.pop()
        petal2 = alsets.pop()

        # Remove conflicting instances of any non-restricted
        # common hints.
        reason = {"stem": stem, "petal1": petal1, "petal2": petal2,
                  "rcs": rcs, "ucs": ucs}
        for hint in ucs:
            overlap = self.als_related(petal1, hint) & self.als_related(petal2, hint)
            if self.test_purge(overlap, set([hint])):
                self.purge_hints(plan, overlap, set([hint]), reason)
                status = True

        return status

    """
    Death Blossom strategy.
    """
    def run(self, plan):
        alsets = self.als_find_in_lots(plan.get_sudoku().get_lots())
        for als1, als2, als3 in itertools.combinations(alsets, 3):
            if any([x.is_complete() for x in als1 | als2 | als3]):
                continue
            if als1 & als2 or als1 & als3 or als2 & als3:
                continue
            if self.death_blossom(plan, set([als1, als2, als3])):
                return True
        return False
