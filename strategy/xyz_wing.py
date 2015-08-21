#
# XYZ-Wing strategy module
#

import itertools
from logger import *
from playbook import *
from sudoku import *

class XYZWing(Strategy):

    __metaclass__ = StrategyMeta

    """
    XYZ-WING involves 3 nodes, namely, XYZ, XZ, and YZ. Each letter in the node
    name refers to a hint. For example, node XYZ has the hints X, Y, and Z.

    XYZ-WING has the following properties.

      1) XZ | YZ == XYZ
      2) XY <-> XZ, XY <-> YZ, but not XZ <-> YZ

    As a result, the hint Z can be eliminated from nodes connected to all of
    XZ, YZ, and XYZ.
    """
    def __init__(self):
        Strategy.__init__(self, "XYZ-WING")

    """
    Validate the XYZ-WING pattern and process it if found.
    """
    def xyz_wing(self, plan, xyz, pair):
        xz, yz = pair

        # 1) XZ | YZ == XYZ
        if xz.get_hints() | yz.get_hints() != xyz.get_hints():
            return False
        # 2) XYZ <-> XZ, XYZ <-> YZ, but not XZ <-> YZ
        if not xyz.is_related(xz) or not xyz.is_related(yz) or xz.is_related(yz):
            return False

        z = xz.get_hints() & yz.get_hints()

        overlap = xyz.find_related() & xz.find_related() & yz.find_related()
        overlap -= set([xyz])
        overlap -= set(pair)

        if self.test_purge(overlap, z):
            reason = {"hint": sorted(z), "xyz": xyz, "xz": xz, "yz": yz}
            self.purge_hints(plan, overlap, z, reason)
            return True

        return False

    """
    Look for and process Y-WING patterns across all nodes with the required
    hints.    
    """
    def run(self, plan):
        status = False

        sudoku = plan.get_sudoku()
        for xyz in [node for node in sudoku.get_incomplete()
                      if len(node.get_hints()) == 3]:
            # In case the hinge node has been updated...
            if xyz.is_complete() or len(xyz.get_hints()) != 3:
                continue

            nodes = [node for node in sudoku.get_incomplete()
                     if len(node.get_hints()) == 2 and node != xyz]
            for pair in itertools.combinations(nodes, 2):
                # In case nodes in the candidate group have been updated...
                if any([x.is_complete() for x in pair]):
                    continue

                if self.xyz_wing(plan, xyz, pair):
                    status = True

        return status
