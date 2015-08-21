#
# Medusa based strategy module
#

import itertools
from logger import *
from playbook import *
from sudoku import *

class MedusaBase(Strategy):

    def __init__(self, name, simple = True):
        Strategy.__init__(self, name)
        self.simple = simple

    """
    Return the set of links in the graph optionally conditioned upon
    hint and color matching. Each link takes the form of a 2-tuple
    with node and hint.
    """
    def medusa_all_links(self, graph, hint = None, color = None):
        return set([l for l, c in graph.keys()
                    if (hint is None or l[1] == hint) and
                    (color is None or c == color)])

    """
    Return True if the link is in the graph.
    """
    def medusa_has_link(self, graph, link):
        for color in [True, False]:
            if (link, color) in graph:
                return True
        return False

    """
    Return the set of all Sudoku nodes in the 3D-MEDUSA graph.
    """
    def medusa_all_nodes(self, graph, hint = None, color = None):
        return set([n for n, h in self.medusa_all_links(graph, hint, color)])

    """
    Return the set of all hints in the 3D-MEDUSA graph. For simple
    coloring, there will be one and only.
    """
    def medusa_all_hints(self, graph, color = None):
        return set([h for n, h in self.medusa_all_links(graph, None, color)])

    """
    Return the set of hints in the 3D-MEDUSA graph in the given
    node and with the given color.
    """
    def medusa_node_hints(self, graph, node, color = None):
        return set([h for x, h in self.medusa_all_links(graph, None, color) if x == node])

    """
    Return the raw "chain" as a list of locations and the connected
    locations for each.
    """
    def medusa_chain(self, graph):
        return graph.items()

    """
    Format the medusa graph for printing.
    """
    def medusa_format(self, graph):
        return ", ".join("{0}[{1}]".format(
                self.medusa_format_loc(k),
                "|".join(self.medusa_format_loc(l) for l in v))
                         for k, v in graph.items())

    """
    Format a single medusa graph node for printing.
    """
    def medusa_format_loc(self, loc):
        (n, h), c = loc
        return "{0}{1}[{2}]".format("+" if c else "-", h, n)

    """
    Purge all hints in the 3D-MEDUSA graph with the given color.
    This should always return True since a 3D-MEDUSA graph should
    have hints of both colors.
    """
    def medusa_purge_color(self, plan, graph, color, reason, note):
        status = False
        for node in self.medusa_all_nodes(graph):
            hints = self.medusa_node_hints(graph, node, color)
            if self.purge_hints(plan, [node], hints, reason, note):
                status = True
        return status

    """
    If two hints in a node have the same color, all hints of that
    color can be removed from the graph.
    """
    def medusa_conflict_node(self, plan, graph, reason):
        for node in self.medusa_all_nodes(graph):
            if node.is_complete():
                continue
            for color in [True, False]:
                hints = self.medusa_node_hints(graph, node, color)
                if len(hints) > 1:
                    note = "hints {0} have color {1} in {2}".format(
                        sorted(hints), color, node)
                    return self.medusa_purge_color(plan, graph, color, reason, note)
        return False

    """
    It the same hint appears twice in the same color in the same lot,
    all hints of that color can be removed from the graph.
    """
    def medusa_conflict_lot(self, plan, graph, reason):
        nodes = self.medusa_all_nodes(graph)
        for lot in plan.get_sudoku().get_lots():
            lnodes = nodes & set(lot.get_nodes())
            for color in [True, False]:
                conflicts = set()
                candidates = [self.medusa_node_hints(graph, node, color) for node in lnodes
                              if not node.is_complete()]
                for pair in itertools.combinations(candidates, 2):
                    conflicts |= pair[0] & pair[1]
                if conflicts:
                    note = "hints {0} have color {1} in {2}".format(
                        sorted(conflicts), color, lot)
                    return self.medusa_purge_color(plan, graph, color, reason, note)
        return False

    """
    Check if a node in the 3D-MEDUSA graph has two conflicting colors.
    """
    def medusa_bicolor_node(self, plan, graph, reason):
        status = False
        for node in self.medusa_all_nodes(graph):
            if node.is_complete():
                continue
            on = self.medusa_node_hints(graph, node, True)
            off = self.medusa_node_hints(graph, node, False)
            if not on or not off:
                continue
            hints = on | off
            if self.test_update([node], hints):
                self.update_hints(plan, [node], hints, reason, "dual-color node")
                status = True
        return status

    """
    Check if a node outside of the 3D-MEDUSA graph can simultaneously
    "see" nodes of conflicting colors.
    """
    def medusa_conflict_offchain(self, plan, graph, reason):
        status = False
        for hint in self.medusa_all_hints(graph):
            on = self.find_related(self.medusa_all_nodes(graph, hint, True))
            off = self.find_related(self.medusa_all_nodes(graph, hint, False))
            intersect = on & off
            hints = set([hint])
            if self.test_purge(intersect, hints):
                self.purge_hints(plan, intersect, hints, reason, "off-chain color conflict")
                status = True
        return status

    """
    If an uncolored hint in a node can see the same hint but colored in
    the lot, and any hint exists in the same node with opposite color,
    we can remove the uncolored hint.
    """
    def medusa_node_lot(self, plan, graph, reason):
        status = False

        nodes = self.medusa_all_nodes(graph)
        for node in nodes:
            if node.is_complete():
                continue
            hints = node.get_hints()
            for color in [True, False]:
                hints -= self.medusa_node_hints(graph, node, color)
            area = node.find_related()
            conflicts = set()
            for hint in hints:
                for color in [True, False]:
                    if not self.medusa_node_hints(graph, node, color):
                        continue
                    intersect = area & self.medusa_all_nodes(graph, hint, not color)
                    if intersect:
                        conflicts.add(hint)
            if self.test_purge([node], conflicts):
                self.purge_hints(plan, [node], conflicts, reason, "node lot conflict")
                status = True

        return status

    """
    Check if a node outside of the 3D-MEDUSA graph is emptied by
    nodes of the same color.
    """
    def medusa_empty_color(self, plan, graph, reason):
        nodes = set(plan.get_sudoku().get_incomplete()) - self.medusa_all_nodes(graph)
        for node in nodes:
            for color in [True, False]:
                status = True
                for hint in node.get_hints():
                    intersect = self.medusa_all_nodes(graph, hint, color) & node.find_related()
                    if not intersect:
                        status = False
                        break
                if status:
                    note = "{0} emptied by color {1}".format(node, color)
                    return self.medusa_purge_color(plan, graph, color, reason, note)
        return False

    """
    Process a 3D-MEDUSA graph.
    """
    def medusa_process(self, plan, graph):
        reason = {"chain": self.medusa_format(graph),
                  "__chain__": self.medusa_chain(graph)}

        status = False

        if not self.simple and self.medusa_conflict_node(plan, graph, reason):
            status = True
        if self.medusa_conflict_lot(plan, graph, reason):
            status = True
        if not self.simple and self.medusa_bicolor_node(plan, graph, reason):
            status = True
        if self.medusa_conflict_offchain(plan, graph, reason):
            status = True
        if self.medusa_node_lot(plan, graph, reason):
            status = True
        if not self.simple and self.medusa_empty_color(plan, graph, reason):
            status = True

        return status

    """
    Return all exclusive links emanating from the given link.
    """
    def medusa_find_links(self, link):
        node, hint = link

        # Look for exclusive links in each lot.
        nodes = [lot.exclusive_link(node, hint) for lot in node.get_lots()]
        nodes = set([n for n in nodes if n])
        links = set([(n, hint) for n in nodes])

        # Look for exclusive link in the node.
        if not self.simple:
            diff = node.get_hints() - set([hint])
            if len(diff) == 1:
                sibling = diff.pop()
                links.add((node, sibling))

        return links

    """
    Add the next location to the graph and return True if it didn't
    exist in the graph before. Meanwhile, make a connection from the
    current location to the next if and only if we didn't come from
    there.
    """
    def medusa_add(self, graph, next, loc = None):
        status = not next in graph
        if status:
            graph[next] = []
        if loc and not loc in graph[next]:
            graph[loc].append(next)
        return status

    """
    Recursive 3D-MEDUSA graph walk. It takes the partially constructed
    graph and a location in the graph and enters all edges emanating
    from that location into the graph. It calls itself if there are any
    new location to be explored. Otherwise, the recursion terminates.
    """
    def medusa_walk(self, loc, graph):
        link, color = loc

        # Add the origin to the graph.
        if not graph:
            self.medusa_add(graph, loc)

        locs = []
        links = self.medusa_find_links(link)
        for next in [(l, not color) for l in links]:
            if self.medusa_add(graph, next, loc):
                locs.append(next)

        for next in locs:
            self.medusa_walk(next, graph)

    """
    Each 3D-MEDUSA instance is a graph. The node in the graph, referred
    to as location henceforth to not confuse with the Sudoku node, is a
    2-tuple of a link and its binary color. The link is a 2-tuple by
    itself of Sudoku node and hint. An edge may connect two locations
    which indicates the existence of an exclusive (or strong) link
    between the two links. The color of the link in a 3D-MEDUSA graph
    always alternates between any pair of connected links. We use a dict
    to represent the 3D-MEDUSA graph.
    
    The 3D-MEDUSA instance is an undirected, fully reachable, and possibly
    cyclic graph. That implies we will eventually cover the entire graph
    regardless where we start.

    A Sudoku instance may have multiple 3D-MEDUSA instances, each of which
    is represented by a separate graph.
    """
    def medusa(self, plan, i):
        graphs = []
        for node in plan.get_sudoku().get_incomplete():
            if not i in node.get_hints():
                continue
            # Skip if the link is part of an already discovered graph.
            # Note that the link color doesn't really matter for this
            # test due to the full reachability of the graph.
            link = (node, i)
            if any([self.medusa_has_link(x, link) for x in graphs]):
                continue
            graph = dict()
            self.medusa_walk((link, True), graph)
            if len(graph) > 1:
                graphs.append(graph)
        
        status = False
        for graph in graphs:
            if self.medusa_process(plan, graph):
                status = True
        return status

    """
    3D-MEDUSA strategy. Simple coloring, or single's chain, as a special
    case of 3D-MEDUSA, is covered here as well.
    """
    def run(self, plan):
        status = False
        for i in range(1, 10):
            if self.medusa(plan, i):
                status = True
        return status

class SimpleColoring(MedusaBase):

    __metaclass__ = StrategyMeta

    def __init__(self):
        MedusaBase.__init__(self, "SIMPLE-COLORING")

class TDMedusa(MedusaBase):

    __metaclass__ = StrategyMeta

    def __init__(self):
        MedusaBase.__init__(self, "3D-MEDUSA", False)
