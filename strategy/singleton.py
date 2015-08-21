#
# Singleton strategy module
#

from logger import *
from playbook import *
from sudoku import *

class Singleton(Strategy):

    __metaclass__ = StrategyMeta

    """
    SINGLETON is the most rudimentary strategy in Sudoku that updates
    the possible set of hints of a node solely based on complete nodes
    in the same lots.

    The strategy is explicitly invoked once at the beginning of the plan
    execution. After that, nodes are kept up to date inline as soone as a
    node reaches completeness. This is because all strategies here rely
    upon the nodes being up to date. A node may be completed in midst of
    a strategy execution. If we don't keep the related nodes updated, we
    may fail as the strategy unravels.
    """
    def __init__(self):
        Strategy.__init__(self, "SINGLETON")

    """
    SINGLETON is the only one-shot strategy, which means that it is
    executed once.
    """
    def one_shot(self):
        return True

    """
    Refresh the given node.
    """
    def singleton(self, plan, node):
        return self.refresh_node(plan, node)

    """
    Refresh all nodes.
    """
    def run(self, plan):
        return any([self.singleton(plan, plan.get_sudoku().get_node(i, j))
                    for i in range(9) for j in range(9)])
