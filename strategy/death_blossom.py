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
    Death Blossom is yet another variation of the strategies based on the
    Almost Locked Set concept.

    For this strategy to work, it requires a total of three ALS's, A, B,
    and C, that can "see" each other. Specifically, there must exist a
    restricted common hint (X) between A and B; and one (Y) between
    A and C; and an unrestricted common hint (Z) between B and C.

    The strategy eliminates all occurrences of hint Z outside of the
    two ALS's, B and C, but can see all instances of Z in both ALS's.

    It differs from ALS in that the two ALS's, B and C, are not directly
    linked to each other. Instead, they are linked via the "stem" A, with
    B and C forming petals around A. Hence, the name Death Blossom.

    It is analagous to XY-WING, where one may consider node XY as the
    stem whereas node XZ and YZ are the petals, except that the parts
    that make Death Blossom are ALS's not nodes.

    Given the added dimension from a third ALS, Death Blossom can be
    orders of magnitude more expensive than plain ALS. To cap the cost,
    an artificial limit is placed on the size of the stem and petals.
    """
    def __init__(self, stem_limit = 1, petal_limit = 4):
        AlmostLockedSet.__init__(self, "DEATH-BLOSSOM")
        self.stem_limit = stem_limit
        self.petal_limit = petal_limit

    """
    Find the stem in the Death Blossom.
    """
    def death_blossom_verify(self, stem, petal1, petal2):
        x, ucs = self.als_urc_hints(petal1, petal2)
        if x or not ucs:
            return None
        rcs1, x = self.als_urc_hints(stem, petal1)
        rcs2, x = self.als_urc_hints(stem, petal2)
        if not rcs1 or not rcs2:
            return None
        rcs = rcs1 | rcs2
        if len(rcs) < 2:
            return None
        ucs -= rcs
        return (rcs, ucs)

    """
    Verify and process the death blossom pattern.
    """
    def death_blossom(self, plan, stem, petal1, petal2):
        status = False

        hsets = self.death_blossom_verify(stem, petal1, petal2)
        if not hsets:
            return status
        rcs, ucs = hsets

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
        lots = plan.get_sudoku().get_lots()

        stems = self.als_find_in_lots(lots, range(1, self.stem_limit + 1))
        petals = self.als_find_in_lots(lots, range(1, self.petal_limit + 1))

        for stem in stems:
            for petal1, petal2 in itertools.combinations(petals, 2):
                if stem & petal1 or stem & petal2 or petal1 & petal2:
                    continue
                if self.death_blossom(plan, stem, petal1, petal2):
                    return True
        return False
