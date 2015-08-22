#
# Fish based strategy module
#

import itertools
from logger import *
from playbook import *
from sudoku import *

class FishBase(Strategy):

    """
    General fish strategy that covers X-WING, SWORD-FISH, JELLY-FISH,
    and even higher order fish in theory.
    """
    def __init__(self, name, dim, fin = False):
        Strategy.__init__(self, name)
        self.dim = dim
        self.fin = fin

    """
    Return the nodes at the intersection of the primary lot and
    the secondary lots ordered by the latter.
    """
    def fish_nodes_ordered(self, plot, slots):
        return [plot.get_node(i) for i in [slot.get_ident() for slot in slots]]

    """
    Similar to above except a set is returned.
    """
    def fish_nodes(self, plot, slots):
        return set(self.fish_nodes_ordered(plot, slots))

    """
    Dump diagnostic info on the fish pattern identified.
    """
    def fish_info(self, plots, slots, hints, fin = None):
        reason = {"hints": hints, "plots": [], "fin": None}
        for plot in plots:
            pnodes = self.fish_nodes_ordered(plot, slots)
            reason["plots"].append({"plot": plot, "nodes": list(pnodes)})
        if fin:
            reason["fin"] = list(fin)
        return reason

    """
    Look for and process fins. A fin represents a small deviation from
    the main fish pattern. In one of the N primary lots, the exclusive
    hints escaped from the fish lattice and spilled into the other nodes
    in the same box around a single lattice point. Only hints from the
    intersection of the secondary lot and the box may be eliminated.
    """
    def fish_fin(self, plan, plots, slots, lhmap):
        status = False

        for plot in plots:
            # Compute the exclusive hints in all but the current plot.
            hints = set.intersection(*[v for k, v in lhmap.items() if k != plot])
            if not hints:
                continue
            # Check if the exclusive hints from the rest of the plots
            # form a fin in the current one. We do that by locating the
            # box around each lattice point in the plot and expand the
            # search for exclusive hints to include the plot nodes within
            # the box.
            pnodes = self.fish_nodes(plot, slots)
            for slot in slots:
                lattice = plot.get_node(slot.get_ident())
                box = lattice.get_box()
                fnodes = set(box.get_nodes()) & set(plot.get_nodes())
                phints = hints & plot.exclusive_hints([node for node in fnodes | pnodes
                                                       if not node.is_complete()])
                if not phints:
                    continue
                # Fin identified. Remove the hints from the rest of the
                # slot (minus the fish) within the box.
                snodes = self.fish_nodes(slot, plots)
                nodes = set(box.get_nodes()) & set(slot.get_nodes()) - snodes
                if self.test_purge(nodes, phints):
                    reason = self.fish_info(plots, slots, phints, fnodes)
                    self.purge_hints(plan, nodes, phints, reason)
                    status = True

        return status

    """
    Look for fish pattern in the given set of primary lots. If found,
    eliminate the hints from the corresponding set of secondary lots.
    If the primary lots are rows, then the secondary lots are columns;
    vice versa. Fins are checked here as well.
    """
    def fish(self, plan, plots, slots):
        # Compute the exclusive hints in the fish lattice along each
        # primary lot.
        lhmap = dict()
        for plot in plots:
            pnodes = self.fish_nodes(plot, slots)
            phints = plot.exclusive_hints([node for node in pnodes if not node.is_complete()])
            lhmap[plot] = phints

        # Compute the intersect of exclusive hints along all primary
        # lots. If the set is non-empty, a fish has been successfully
        # identified.
        hints = set.intersection(*lhmap.values())
        if hints:
            reason = self.fish_info(plots, slots, hints)
            status = False
            for slot in slots:
                snodes = self.fish_nodes(slot, plots)
                others = slot.other_nodes(snodes)
                if self.test_purge(others, hints):
                    self.purge_hints(plan, others, hints, reason)
                    status = True
            return status

        # No fish identified. Now check for fins.
        if self.fin:
            return self.fish_fin(plan, plots, slots, lhmap)

        return False

    """
    Identify and process fish patterns across all combinations of
    N dimensional lattice.
    """
    def run(self, plan):
        status = False
        sudoku = plan.get_sudoku()
        for rows in itertools.combinations(range(9), self.dim):
            for cols in itertools.combinations(range(9), self.dim):
                # Row oriented.
                if self.fish(plan, [sudoku.get_row(i) for i in rows],
                             [sudoku.get_col(j) for j in cols]):
                    status = True
                # Column oriented.
                if self.fish(plan, [sudoku.get_col(j) for j in cols],
                             [sudoku.get_row(i) for i in rows]):
                    status = True
        return status

class XWing(FishBase):

    __metaclass__ = StrategyMeta

    def __init__(self):
        FishBase.__init__(self, "X-WING", 2)

class SwordFish(FishBase):

    __metaclass__ = StrategyMeta

    def __init__(self):
        FishBase.__init__(self, "SWORD-FISH", 3)

class JellyFish(FishBase):

    __metaclass__ = StrategyMeta

    def __init__(self):
        FishBase.__init__(self, "JELLY-FISH", 4)

class FinnedXWing(FishBase):

    __metaclass__ = StrategyMeta

    def __init__(self):
        FishBase.__init__(self, "FINNED X-WING", 2, True)

class FinnedSwordFish(FishBase):

    __metaclass__ = StrategyMeta

    def __init__(self):
        FishBase.__init__(self, "FINNED SWORD-FISH", 3, True)
