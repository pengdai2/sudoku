#
# Almost Locked Set (ALS) base module
#

import itertools
from logger import *
from playbook import *
from sudoku import *

class AlmostLockedSet(Strategy):

    """
    Almost Locked Set, or ALS, is formed when

      1) # of hints in the set is one over # of nodes
      2) nodes in the set can see each other

    When the extra hint is removed from the ALS, it is reduced to a
    locked set, such as a naked or hidden group.

    Multiple ALS's may share common hints. A restricted common hint
    refers to one where all instances of the hint across all ALS's
    involved can see each other. Hence, a restricted common hint
    must be exclusive to one ALS only. Two ALS's sharing a restricted
    common hint are strongly or exclusively linked.

    Conversely, instances of an unrestricted common hint may not all
    see each other; as a result, it may be taken in more than one ALS.

    The basic concept of ALS is widely applied in a number of Sudoku
    strategies, such as Y-WING, XYZ-WING, WXYZ-WING, ALS, APE, Death
    Blossom, which justifies the existence of this common base.
    """
    def __init__(self, name):
        Strategy.__init__(self, name)

    """
    Return the set of hints in the ALS.
    """
    def als_all_hints(self, als):
        return set.union(*[x.get_hints() for x in als if not x.is_complete()])

    """
    Return the set of all unique ALS's in the given lots. If a list
    of sizes is specified, only those ALS's of the desired sizes are
    returned.
    """
    def als_find_in_lots(self, lots, sizes = None):
        alsets = set()
        for lot in lots:
            alsets |= self.als_do_find(lot.get_incomplete(), sizes, True)
        return alsets

    """
    Return the set of all unique ALS's among the given nodes, some of
    which may be complete and not all of which have to be related.
    """
    def als_find_in_nodes(self, nodes, sizes = None):
        nodes = [x for x in nodes if not x.is_complete()]
        return self.als_do_find(nodes, sizes)

    """
    Helper function.
    """
    def als_do_find(self, nodes, sizes = None, related = False):
        alsets = set()
        lens = sizes if sizes else [x + 1 for x in range(len(nodes))]
        for i in lens:
            for als in itertools.combinations(nodes, i):
                if self.als_formed(als, related):
                    alsets.add(frozenset(als))
        return alsets

    """
    Return True if the given nodes form an ALS.
    """
    def als_formed(self, nodes, related = False):
        hints = self.als_all_hints(nodes)
        if len(hints) != len(nodes) + 1:
            return False
        if related:
            return True
        return all([x.is_related(y) for x in nodes for y in nodes if y != x])

    """
    Return the restricted and unrestricted common hints between the
    two ALS's.
    """
    def als_urc_hints(self, als1, als2):
        hints1 = self.als_all_hints(als1)
        hints2 = self.als_all_hints(als2)
        intersect = hints1 & hints2

        rcs = set()
        for hint in intersect:
            nodes1 = [x for x in als1 if x.has_hint(hint)]
            nodes2 = [x for x in als2 if x.has_hint(hint)]
            if all([x.is_related(y) for x in nodes1 for y in nodes2]):
                rcs.add(hint)

        return (rcs, intersect - rcs)

    """
    Return True if the two ALS's are exclusively linked, i.e., sharing
    a restricted common hint.
    """
    def als_linked(self, als1, als2):
        rcs, ucs = self.als_urc_hints(als1, als2)
        return bool(rcs)

    """
    Return the set of nodes that can see all instances of the given
    hint in the ALS.
    """
    def als_related(self, als, hint):
        return self.join_related([x for x in als if x.has_hint(hint)])

    """
    Return the hinge that comprises nodes that can see all other nodes.
    """
    def als_hinge(self, als1, als2):
        hinge1 = set([x for x in als1 if all([x.is_related(y) for y in als2])])
        hinge2 = set([x for x in als2 if all([x.is_related(y) for y in als1])])
        return hinge1 | hinge2
