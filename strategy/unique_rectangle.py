#
# Unique Rectangle strategy module
#

import itertools
from logger import *
from playbook import *
from sudoku import *

class UniqueRectangle(Strategy):

    __metaclass__ = StrategyMeta

    """
    UNIQUE-RECTANGLE takes advantage of the fact that published Sudokus
    have only one solution. A Deadly Pattern is one which allows multiple
    solutions and therefore breaks the Sudoku promise. This strategy takes
    advantage of a Deadly Pattern by using it to eliminate otherwise
    possible hints.

    There are some basic requirements for UNIQUE RECTANGLE. For example,

      1) All four nodes in the rectangle must include the conjugate pair.
      2) At least one node must have the congugate pair only.
      3) Either two rows or two cols must reside in the same box.

    Beyond these traints, there are many variations of UNIQUE RECTANGLE.
    For details of how this strategy works, please refer to sudokuwiki.
    """
    def __init__(self):
        Strategy.__init__(self, "UNIQUE-RECTANGLE")
        
    """
    Process the unique rectangle with the specified floor, roof, and hints.
    This covers all 4 types of unique rectangle as well as type 2 hidden
    unique rectangle, where a floor and roof are available.
    """
    def unique_rectangle_process(self, plan, floor, roof, hints):
        reason = {"hints": sorted(hints), "floor": floor, "roof": roof}

        fl, fr = floor
        rl, rr = roof

        # Unique Type 1.
        for x, y in ((rl, rr), (rr, rl)):
            if len(x.get_hints()) == 2:
                return self.purge_hints(plan, [y], hints, reason, "type 1")

        overlap = self.join_related(roof)

        # Unique Type 2.
        if rl.get_hints() == rr.get_hints() and len(rl.get_hints()) == 3:
            diff = rl.get_hints() - hints
            return self.purge_hints(plan, overlap, diff, reason, "type 2")

        # Unique Type 3.        
        diff = rl.get_hints() | rr.get_hints() - hints
        if len(diff) == 2:
            for node in overlap:
                if node.get_hints() == diff:
                    return self.purge_hints(plan, overlap, diff, reason, "type 3")

        # Unique Type 4.
        excl = hints & self.exclusive_hints(roof)
        if excl:
            return self.unique_rectangle_purge(plan, roof, hints - excl, reason, "type 4")

        # Hidden Type 2.
        for x, y in ((fl, rl), (fr, rr)):
            excl = hints & self.exclusive_hints((x, y))
            if excl:
                return self.purge_hints(plan, [n for n in roof if n != y],
                                        hints - excl, reason, "hidden 2")

    """
    Process the hidden unique rectangle type 1 case which doesn't
    have floor and roof. Instead, it has a single node, the anchor,
    with the conjugate pair only. To qualify, the node diagonal from
    the anchor must have a strong link to each of the remaining two
    nodes by one of the hints in the conjugate pair.
    """
    def hidden_rectangle_process(self, plan, main, pair, hints):
        anchor, diagonal = main

        excl = self.exclusive_hints((diagonal, pair[0]))
        excl &= self.exclusive_hints((diagonal, pair[1]))
        excl &= hints
        if not excl:
            return False

        # Hidden Type 1.
        reason = {"hints": sorted(hints), "floor": main, "roof": pair}
        return self.purge_hints(plan, [diagonal], hints - excl, reason, "hidden 1")

    """
    Check if the given nodes form UNIQUE RECTANGLE and process it
    if so.
    """
    def unique_rectangle(self, plan, nodes):
        # a --- b
        # |     |
        # c --- d
        a, b, c, d = nodes

        # Either pair of the edges must fit into a single box.
        if a.get_box() != b.get_box() and a.get_box != c.get_box():
            return False

        # Every node must have the conjugate pair among other hints.
        hints = self.join_hints(nodes)
        if len(hints) != 2:
            return False

        # At least one node with 2 hints only.
        if all([len(x.get_hints()) > 2 for x in nodes]):
            return False

        # Identify the floor.
        for x, y in ((a, b), (c, d), (a, c), (b, d)):
            if len(x.get_hints()) == 2 and len(y.get_hints()) == 2:
                floor = (x, y)
                roof = [node for node in nodes if not node in floor]
                return self.unique_rectangle_process(plan, floor, roof, hints)

        # Try hidden type 1 if no floor is found.
        for x, y in ((a, d), (d, a), (b, c), (c, b)):
            if len(x.get_hints()) == 2:
                main = (x, y)
                pair = [node for node in nodes if not node in main]
                return self.hidden_rectangle_process(plan, main, pair, hints)

        return False

    """
    Look for and process UNIQUE RECTANGLE in the space of all
    2x2 lattices.
    """
    def run(self, plan):
        status = False
        for rows in itertools.combinations(range(9), 2):
            for cols in itertools.combinations(range(9), 2):
                nodes = [plan.get_sudoku().get_node(i, j) for i in rows for j in cols]
                if any([x.is_complete() for x in nodes]):
                    continue
                if self.unique_rectangle(plan, nodes):
                    status = True
        return status
