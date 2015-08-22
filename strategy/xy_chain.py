#
# XY-Chain strategy module
#

import itertools
from logger import *
from playbook import *
from sudoku import *

class XYChain(Strategy):

    __metaclass__ = StrategyMeta

    """
    XY-CHAIN is an extension of (X)Y-WING in which the node XY is replaced
    by a chain of one or more bi-value nodes linked together. For example,
    XZ -> XA -> AB -> BC -> ... -> WY -> YZ. It's essentially a chain with
    alternating strong and weak links. The strong links are created within
    a node due to bi-value nature and the weak links between nodes due to
    visibility. As such, Z has to be on in either end of the chain.
    """
    def __init__(self):
        Strategy.__init__(self, "XY-CHAIN")

    """
    Recursively walk the chain. Return True if the tail node is reached or
    False when all qualifying links have been exhausted.
    """
    def xy_chain_walk(self, chain, tail, hint, z):
        link = chain[-1]
        for node in link.find_related():
            if node.is_complete() or node in chain:
                continue
            # The next link must be a bi-value link with the hint we are
            # looking for.
            if len(node.get_hints()) > 2 or not hint < node.get_hints():
                continue
            # We must connect with the tail via Y instead of Z
            if node == tail and hint != z:
                return chain + [node]
            res = self.xy_chain_walk(chain + [node], tail, node.get_hints() - hint, z)
            if res:
                return res
        return None

    """
    Search for XY-CHAIN between the pair of nodes and process it
    if found.
    """
    def xy_chain(self, plan, pair):
        status = False

        xz, yz = pair[0], pair[1]
        for candidate in xz.get_hints() & yz.get_hints():
            if xz.is_complete() or yz.is_complete():
                break

            z = set([candidate])
            x = xz.get_hints() - z

            chain = self.xy_chain_walk([xz], yz, x, z)
            if not chain:
                continue

            overlap = xz.find_related() & yz.find_related()
            overlap -= set(pair)

            if self.test_purge(overlap, z):
                reason = {"hint": z, "xz": chain[0], "yz": chain[-1], "chain": chain[1:]}
                self.purge_hints(plan, overlap, z, reason)
                status = True

        return status

    """
    Look for and process XY-CHAIN across all nodes with the required
    hints.
    """
    def run(self, plan):
        status = False
        nodes = [node for node in plan.get_sudoku().get_incomplete()
                 if len(node.get_hints()) == 2]
        for pair in itertools.combinations(nodes, 2):
            # In case nodes in the candidate group have been updated...
            if any([x.is_complete() for x in pair]):
                continue
            if self.xy_chain(plan, pair):
                status = True
        return status
