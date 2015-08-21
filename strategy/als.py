#
# Almost Locked Set (ALS) strategy module
#

import itertools
from logger import *
from playbook import *
from sudoku import *

class ALS(Strategy):

    __metaclass__ = StrategyMeta

    """
    Almost Locked Set, or ALS, is formed when

      1) # of hints in the set is one over # of nodes
      2) nodes in the set can see each other

    For this strategy to work, it requires two ALS's that can "see"
    each other. Specifically, there must exist a restricted common
    hint (X) and a non-restricted common hint (Z) between the two
    ALS's. A restricted common hint refers to one where all instances
    in both ALS's can see each other. Hence, a restricted common hint
    must be exclusive to one ALS.

    The strategy eliminates all occurrences of hint Z outside of the
    two ALS's but can see all instances of Z in both ALS's.
    """
    def __init__(self):
        Strategy.__init__(self, "ALS")

    """
    Process the pair of ALS's.
    """
    def als_process(self, plan, als1, hints1, als2, hints2):
        status = False

        # Make sure the two ALS's are not overlapping.
        if als1 & als2:
            return status

        # Make sure they have at least two common hints.
        intersect = hints1 & hints2
        if len(intersect) < 2:
            return status

        # Find the restricted common hint.
        restricted = set()
        for hint in intersect:
            nodes1 = [x for x in als1 if x.has_hint(hint)]
            nodes2 = [x for x in als2 if x.has_hint(hint)]
            if all([x.is_related(y) for x in nodes1 for y in nodes2]):
                restricted.add(hint)
        if len(restricted) != 1:
            return status

        # Remove conflicting instances of any non-restricted
        # common hints.
        reason = {"als1": sorted(als1), "als2": sorted(als2), "restricted": sorted(restricted)}
        for hint in intersect - restricted:
            nodes1 = [x for x in als1 if x.has_hint(hint)]
            nodes2 = [x for x in als2 if x.has_hint(hint)]
            overlap = self.join_related(nodes1) & self.join_related(nodes2)
            if self.test_purge(overlap, set([hint])):
                self.purge_hints(plan, overlap, set([hint]), reason)
                status = True
        return status

    """
    Find all ALS instances.
    """
    def find_all(self, plan):
        all = dict()
        for lot in plan.get_sudoku().get_lots():
            nodes = lot.get_incomplete()
            for i in range(len(nodes)):
                for group in itertools.combinations(nodes, i + 1):
                    hints = set.union(*[x.get_hints() for x in group])
                    if len(hints) == len(group) + 1:
                        all[frozenset(group)] = hints
        return all

    """
    ALS strategy.
    """
    def run(self, plan):
        all = self.find_all(plan)
        for als1, als2 in itertools.combinations(all.keys(), 2):
            hints1 = all[als1]
            hints2 = all[als2]
            if self.als_process(plan, als1, hints1, als2, hints2):
                return True
        return False
