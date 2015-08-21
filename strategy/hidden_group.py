#
# Hidden Group strategy module
#

import itertools
from logger import *
from playbook import *
from sudoku import *

class HiddenGroup(Strategy):

    __metaclass__ = StrategyMeta

    """
    HIDDEN-GROUP, including single, pair, triple, quad, etc. Hidden in
    this context refers to all the remaining hints in the group of
    nodes. It is in contrast to naked. A hidden group has more hints
    among them than the number of nodes in the group. At the same time,
    it includes all the hints necessary to form a naked group. The extra
    hints are simple smoke screens that mask the fact hidden underneath.
    """
    def __init__(self):
        Strategy.__init__(self, "HIDDEN-GROUP")

    """
    Find all hidden groups in the given lot. Since the all remaining
    nodes must be a naked group of its own, the size of the naked
    groups we are looking for should be less than the total number
    of incomplete nodes.
    """
    def find_hidden_groups(self, lot):
        groups = []

        nodes = set(lot.get_incomplete())
        for i in range(1, len(nodes)):
            # Look for hidden group of size i in the remaining nodes.
            for candidate in [set(x) for x in itertools.combinations(nodes, i)]:
                # Skip candidate with nodes that are members of another group.
                if not candidate <= nodes:
                    continue

                # Values are said to be exclusive to a group if they cannot appear
                # in all other nodes in the lot. The exclusive set can be found
                # by computing the set difference between the union of the group
                # and all other nodes in the lot. By definition, the exclusive set
                # must have a cardinality of no more than the group size.
                hints = lot.exclusive_hints(candidate)
                if len(hints) > len(candidate):
                    raise LogicException(lot)
                elif len(hints) < len(candidate):
                    continue

                # If it is the same as the group size, we either have a naked or
                # a hidden group, depending on the where there are excess hints in
                # the group beyond those in the exclusive set.
                if self.all_hints(candidate) > hints:
                    groups.append((hints, candidate))

                # Remove the candidate nodes so tbey won't form another group.
                nodes -= candidate

        return groups

    """
    Find and process hidden groups within the given lot. Once a hidden group
    is found, the excess hints are removed from it, which then strips it down
    to a naked group.
    """
    def hidden_group(self, plan, lot):
        status = False

        for hints, group in self.find_hidden_groups(lot):
            if self.test_update(group, hints):
                reason = {"hints": sorted(hints), "group": list(group)}
                self.update_hints(plan, group, hints, reason)
                status = True

        return status

    """
    Process hidden groups across all lots.
    """
    def run(self, plan):
        return any([self.hidden_group(plan, lot)
                    for lot in plan.get_sudoku().get_lots()])
