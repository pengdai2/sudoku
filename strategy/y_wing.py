#
# Y-Wing strategy module
#

import itertools
from logger import *
from playbook import *
from sudoku import *

class YWing(Strategy):

    __metaclass__ = StrategyMeta

    """
    Y-WING involves 3 nodes, namely, XY, XZ, and YZ. Each letter in the node
    name refers to a hint. For example, node XY has the hints X and Y.

    Y-WING has the following properties.

      1) XY ^ XZ == YZ
      2) XY <-> XZ, XY <-> YZ, but not XZ <-> YZ

    As a result, the hint Z can be eliminated from nodes connected to both
    XZ and YZ.
    """
    def __init__(self):
        Strategy.__init__(self, "Y-WING")

    """
    Validate the Y-WING pattern and process it if found.
    """
    def y_wing(self, plan, candidate):
        for i in range(3):
            # Y-WING requires 3 nodes, XY, XZ, YZ with the following properties.
            xy = candidate[i]
            xz = candidate[(i + 1) % 3]
            yz = candidate[(i + 2) % 3]

            # 1) XY ^ XZ == YZ
            if xy.get_hints() ^ xz.get_hints() != yz.get_hints():
                continue
            # 2) XY <-> XZ, XY <-> YZ, but not XZ <-> YZ
            if not xy.is_related(xz) or not xy.is_related(yz) or xz.is_related(yz):
                continue

            z = xz.get_hints() & yz.get_hints()

            overlap = xz.find_related() & yz.find_related()
            overlap -= set(candidate)

            if self.test_purge(overlap, z):
                reason = {"hint": sorted(z), "xy": xy, "xz": xz, "yz": yz}
                self.purge_hints(plan, overlap, z, reason)
                return True

        return False

    """
    Look for and process Y-WING patterns across all nodes with the required
    hints.
    """
    def run(self, plan):
        status = False

        # Limit the Y-WING check to nodes with 2 hints only.
        nodes = [node for node in plan.get_sudoku().get_incomplete()
                 if len(node.get_hints()) == 2]
        for candidate in itertools.combinations(nodes, 3):
            # In case nodes in the candidate group have been updated...
            if any([node.is_complete() for node in candidate]):
                continue

            if self.y_wing(plan, candidate):
                status = True

        return status
