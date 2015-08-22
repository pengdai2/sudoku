#
# Aligned Pair Exclusion (APE) strategy module
#

import itertools
from logger import *
from playbook import *
from sudoku import *
from almost_locked_set import *

class APE(AlmostLockedSet):

    __metaclass__ = StrategyMeta

    """
    ALIGNED PAIR EXCLUSION, or APE, can be succinctly stated: Any two nodes
    that can see each other CANNOT duplicate the contents of any Almost
    Locked Set they both entirely see and share hints with.

    The strategy works by enumerating all combinations of hints among the
    pair of nodes and then eliminate some via conflict with ALS.
    """
    def __init__(self):
        AlmostLockedSet.__init__(self, "APE")

    """
    Check if the given pair of hints, one for each node in the aligned pair,
    can be eliminated by an ALS.
    """
    def ape_exclude(self, alsets, hints):
        for als in alsets:
            if hints <= self.als_all_hints(als):
                return als
        return None

    """
    Exclude hints from the given pair of nodes.
    """
    def ape(self, plan, pair):
        node, other = pair

        # Look for ALS's among those both nodes in the pair can see.
        overlap = [x for x in node.find_related() & other.find_related() if not x in pair]
        alsets = self.als_find_in_nodes(overlap)
        if not alsets:
            return False

        hints = set()
        excl = list()
        for candidate in [(h, o) for h in node.get_hints() for o in other.get_hints()]:
            if candidate[0] == candidate[1]:
                # "Unaligned" APE.
                if not node.is_related(other):
                    hints.add(candidate)
                continue
            als = self.ape_exclude(alsets, set(candidate))
            if not als:
                hints.add(candidate)
            else:
                excl.append((candidate, sorted(als)))

        nhints = set([h for h, o in hints])
        ohints = set([o for h, o in hints])
        if self.test_update([node], nhints) or self.test_update([other], ohints):
            reason = {"pair": pair, "excl": excl}
            self.update_hints(plan, [node], nhints, reason)
            self.update_hints(plan, [other], ohints, reason)
            return True

        return False

    """
    Look for and process APE pairs across all nodes.
    """
    def run(self, plan):
        status = False
        nodes = plan.get_sudoku().get_incomplete()
        for pair in itertools.combinations(nodes, 2):
            if any([x.is_complete() for x in pair]):
                continue
            if self.ape(plan, pair):
                status = True
        return status
