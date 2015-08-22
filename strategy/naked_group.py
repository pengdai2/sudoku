#
# Naked Group strategy module
#

import itertools
from logger import *
from playbook import *
from sudoku import *

class NakedGroup(Strategy):

    __metaclass__ = StrategyMeta

    """
    NAKED-GROUP, including single, pair, triple, quad, etc. Naked in
    this context refers to all the remaining hints in the group of
    nodes. A naked group has the same number of hints among them as
    the number of nodes in the group.

    For example, a naked single refers to the degenerate case where a
    node has but one hint left such that the value of the node is known.
    A naked pair, also known as a conjugate pair, is a set of two nodes
    with two hints that belong to at least one lot. A naked triple is
    any group of three nodes that contain in total three hints. Etc. etc.

    The hints carried within a naked group are exclusive to the nodes
    within the said group. In other words, they mustn't appear elsewhere
    in the lot. Hence, we can eliminate the hints beyond the group.
    """

    def __init__(self):
        Strategy.__init__(self, "NAKED-GROUP")

    """
    Find all naked groups in the given lot. Since we are using the
    naked group strategy to eliminate hints from nodes outside the
    group, the size of the naked groups we are looking for should be
    less than the total number of incomplete nodes.
    """
    def find_naked_groups(self, lot):
        groups = []

        nodes = set(lot.get_incomplete())
        for i in range(1, len(nodes)):
            # Find all naked groups of size i.
            for candidate in [set(x) for x in itertools.combinations(nodes, i)]:
                # Skip candidate with nodes that are members of another group.
                if not candidate <= nodes:
                    continue

                # Naked group has number of hints equal to the size of the group.
                hints = self.all_hints(candidate)
                if len(hints) < len(candidate):
                    raise LogicException(self)
                if len(hints) > len(candidate):
                    continue

                groups.append((hints, candidate))

                # Remove the candidate nodes so tbey won't form another group.
                nodes -= candidate

        return groups

    """
    Find and process naked groups within the given lot. Once a naked
    group is found, its hints are eliminated elsewhere in the lot.
    """
    def naked_group(self, plan, lot):
        status = False

        for hints, group in self.find_naked_groups(lot):
            nodes = lot.other_nodes(group)
            if self.test_purge(nodes, hints):
                reason = {"hints": hints, "group": group}
                self.purge_hints(plan, nodes, hints, reason)
                status = True

        return status

    """
    Process naked groups across all lots.
    """
    def run(self, plan):
        return any([self.naked_group(plan, lot)
                    for lot in plan.get_sudoku().get_lots()])
