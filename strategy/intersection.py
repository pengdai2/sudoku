#
# Intersection strategy module
#

from logger import *
from playbook import *
from sudoku import *

class Intersection(Strategy):

    __metaclass__ = StrategyMeta

    def __init__(self):
        Strategy.__init__(self, "INTERSECTION")

    """
    Divide the given lot into groups of 3 consecutive nodes for
    purpose of intersection with a corresponding lot and return
    the group of nodes identified by i. The index i is in range(3)
    in increasing order from left to right or top to bottom. In
    case of a box, the nodes are split vertically when transposed
    is set to True.
    """
    def intersection_nodes(self, lot, i, transposed = False):
        if not transposed:
            return [x for x in [lot.get_node(i * 3 + j) for j in range(3)] if not x.is_complete()]
        else:
            return [x for x in [lot.get_node(j * 3 + i) for j in range(3)] if not x.is_complete()]

    """
    Process intersection between the given row or col and
    the corresponding boxes.
    """
    def intersect_line(self, plan, lot):
        status = False
        for i in range(3):
            nodes = self.intersection_nodes(lot, i)
            if not nodes:
                continue
            hints = lot.exclusive_hints(nodes)
            if not hints:
                continue
            box = nodes[0].get_box()
            others = box.other_nodes(nodes)
            if self.test_purge(others, hints):
                reason = {"hints": sorted(hints), "lots": [lot, box], "nodes": nodes}
                self.purge_hints(plan, others, hints, reason)
                status = True
        return status

    """
    Process intersection between the given box and the corresponding
    rows and cols.
    """
    def intersect_box(self, plan, lot):
        status = False
        for i in range(3):
            nodes = self.intersection_nodes(lot, i)
            if not nodes:
                continue
            hints = self.exclusive_hints(nodes)
            if not hints:
                continue
            row = nodes[0].get_row()
            others = row.other_nodes(nodes)
            if self.test_purge(others, hints):
                reason = {"hints": sorted(hints), "lots": [lot, row], "nodes": nodes}
                self.purge_hints(plan, others, hints, reason)
                status = True

        for j in range(3):
            nodes = self.intersection_nodes(lot, j, True)
            if not nodes:
                continue
            hints = self.exclusive_hints(nodes)
            if not hints:
                continue
            col = nodes[0].get_col()
            others = col.other_nodes(nodes)
            if self.test_purge(others, hints):
                reason = {"hints": sorted(hints), "lots": [lot, col], "nodes": nodes}
                self.purge_hints(plan, others, hints, reason)
                status = True

        return status

    """
    Process INTERSECTION across all lots.
    """
    def run(self, plan):
        sudoku = plan.get_sudoku()
        return any([self.intersect_line(plan, x) for x in sudoku.get_rows()] +
                   [self.intersect_line(plan, x) for x in sudoku.get_cols()] +
                   [self.intersect_box(plan, x) for x in sudoku.get_boxes()])
