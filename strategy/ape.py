#
# Aligned Pair Exclusion (APE) strategy module
#

import itertools
from logger import *
from playbook import *
from sudoku import *

class APE(Strategy):

    __metaclass__ = StrategyMeta

    """
    ALIGNED PAIR EXCLUSION, or APE, can be succinctly stated: Any two nodes
    that can see each other CANNOT duplicate the contents of any Almost
    Locked Set they both entirely see and share hints with.

    Almost Locked Set, or ALS, is formed when

      1) # of hints in the set is one over # of nodes
      2) nodes in the set can see each other

    The strategy works by enumerating all combinations of hints among the
    pair of nodes and then eliminate some via conflict with ALS.
    """
    def __init__(self):
        Strategy.__init__(self, "APE")

    """
    Check if an Almost Locking Set, or ALS, is formed among the nodes.
    """
    def ape_als_formed(self, nodes, hints):
        if len(hints) > len(nodes) + 1:
            return False
        return all([x.is_related(y) for x in nodes for y in nodes if y != x])

    """
    Check if the given pair of hints, one from each node in the APE, can be
    eliminated via an ALS in the overlap are visible to both nodes.
    """
    def ape_exclude(self, pair, overlap):
        for i in range(len(overlap)):
            for nodes in itertools.combinations(overlap, i + 1):
                hints = set.union(*[x.get_hints() for x in nodes])
                if not self.ape_als_formed(nodes, hints):
                    continue
                # Check if the pair consumes two hints of the ALS
                if hints >= set(pair):
                    return nodes
        return None
    
    """
    Exclude hints from the given pair of nodes.
    """
    def ape(self, plan, pair):
        node, other = pair
        if node.is_complete() or other.is_complete():
            return False

        overlap = set([x for x in node.find_related() & other.find_related()
                       if not x.is_complete() and not x in pair])
        if not overlap:
            return False

        hints = set()
        excl = list()
        for candidate in [(h, o) for h in node.get_hints() for o in other.get_hints()]:
            if candidate[0] == candidate[1]:
                # "Unaligned" APE.
                if not node.is_related(other):
                    hints.add(candidate)
                continue
            als = self.ape_exclude(candidate, overlap)
            if not als:
                hints.add(candidate)
            else:
                excl.append((candidate, als))

        nhints = set([h for h, o in hints])
        ohints = set([o for h, o in hints])
        if self.test_update([node], nhints) or self.test_update([other], ohints):
            reason = {"pair": pair, "excl": excl}
            self.update_hints(plan, [node], nhints, reason)
            self.update_hints(plan, [other], ohints, reason)
            return True

        return False

    """
    Look for and process APE pairs across all nodes with the required
    hints.
    """
    def run(self, plan):
        return any([self.ape(plan, pair)
                    for pair in itertools.combinations(plan.get_sudoku().get_incomplete(), 2)])
