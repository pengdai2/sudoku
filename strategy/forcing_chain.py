#
# Forcing Chain strategy module
#

from logger import *
from playbook import *
from sudoku import *
from chain import *

class ForcingChain(Chain):

    """
    FORCING CHAIN covers a family of chain based strategies. Unlike
    AIC, which relies on the formation of Nice Loops, it constructs
    multiple alternating inteference chains between two sets of
    links and identifes conflicts that lead to the elimination of
    otherwise possible hints. The different FORCING CHAIN strategies
    vary in terms of the selection of the origin and detination sets
    of links and colors.

    To support FORCING CHAIN, we start from a given link and construct
    a web of connected, or chained, links. While doing so, we building
    out the web, we maintain back links from any link to the one that
    led to its discovery. Using these back links, we can easily find
    a path from any link to the origin as long as the link is in the
    chain web.
    """
    def __init__(self, name, biloc_only = False, group_limit = 1):
        Chain.__init__(self, name, biloc_only, group_limit)

    """
    Add a link between the specified locations in the forcing chain.
    """
    def forcing_chain_add_link(self, chain, loc, to, forward = True):
        if not loc in chain:
            chain[loc] = ([], [])
        fore, back = chain[loc]
        if forward:
            fore.append(to)
        else:
            back.append(to)

    """
    Check if the specified location is in the forcing chain.
    """
    def forcing_chain_has_link(self, chain, loc):
        return loc in chain

    """
    Return the original back link from the specified location. The
    original back link leads to the location in the forcing chain
    from which this location is first discovered. Hence, it's always
    the first item in the back list. The origin of the forcing chain
    has no back links.
    """
    def forcing_chain_back_link(self, chain, loc):
        fore, back = chain[loc]
        return back[0] if back else None

    """
    Find a path leading from the origin to the specified location by
    following the back link in the forcing chain.
    """
    def forcing_chain_find_path(self, chain, loc):
        path = [loc]
        while True:
            loc = self.forcing_chain_back_link(chain, loc)
            if not loc:
                break
            path.insert(0, loc)
        return path

    """
    Construct the path in the forcing chain that leads from origin
    to the specified location and return the string format.
    """
    def forcing_chain_format(self, chain, loc, verbose = True):
        path = self.forcing_chain_find_path(chain, loc)
        return self.chain_format(path, verbose)

    """
    Find the next set of links to walk from the specified location.
    """
    def forcing_chain_find_links(self, chain, loc):
        count = 0
        if self.forcing_chain_has_link(chain, loc):
            path = self.forcing_chain_find_path(chain, loc)
            count = len(self.chain_group_links(path))
        return self.chain_find_links(loc[0], count)

    """
    Recursively walk the forcing chain that started from the origin
    and has reached the given location.
    """
    def forcing_chain_walk(self, loc, chain):
        link, color = loc

        slinks, wlinks, glinks = self.forcing_chain_find_links(chain, loc)
        wlinks |= slinks
        slinks |= glinks

        links = wlinks if color else slinks

        nlocs = set()
        for next in links:
            to = (next, not color)
            if self.forcing_chain_has_link(chain, to):
                continue
            self.forcing_chain_add_link(chain, loc, to, True)
            self.forcing_chain_add_link(chain, to, loc, False)
            nlocs.add(to)

        for nloc in nlocs:
            self.forcing_chain_walk(nloc, chain);

class NishioForcingChain(ForcingChain):

    __metaclass__ = StrategyMeta

    def __init__(self):
        ForcingChain.__init__(self, "NISHIO FORCING-CHAIN", False, 2)

    """
    Check for conflicting color for the same hint in the node.
    """
    def nishio_node_multi_color(self, plan, origin, chain, node):
        (group, i), color = origin
        for hint in node.get_hints():
            locs = [(((node, ), hint), c) for c in [True, False]]
            if all([self.forcing_chain_has_link(chain, x) for x in locs]):
                if self.test_purge(set(group), set([i])):
                    reason = self.nishio_info(chain, locs)
                    self.purge_hints(plan, set(group), set([i]), reason, "node multi color")
                    return True
        return False

    """
    Check for more than one hint in the node with color True.
    """
    def nishio_node_multi_hint(self, plan, origin, chain, node):
        (group, i), color = origin
        locs = set()
        for loc in [(((node, ), h), True) for h in node.get_hints()]:
            if self.forcing_chain_has_link(chain, loc):
                locs.add(loc)
        if len(locs) > 1:
            if self.test_purge(set(group), set([i])):
                reason = self.nishio_info(chain, locs)
                self.purge_hints(plan, set(group), set([i]), reason, "node multi hint")
                return True
        return False

    """
    Check for all hints in the node with color False.
    """
    def nishio_node_excl_hint(self, plan, origin, chain, node):
        (group, i), color = origin
        locs = [(((node, ), h), False) for h in node.get_hints()]
        if all([self.forcing_chain_has_link(chain, x) for x in locs]):
            if self.test_purge(set(group), set([i])):
                reason = self.nishio_info(chain, locs)
                self.purge_hints(plan, set(group), set([i]), reason, "node excl hint")
                return True
        return False

    """
    Check for more than one occurrence of a hint in the lot with
    color True.
    """
    def nishio_lot_multi_hint(self, plan, origin, chain, lot):
        (group, i), color = origin
        hlmap = dict()
        for node in lot.get_nodes():
            if node.is_complete():
                continue
            for hint in node.get_hints():
                loc = (((node, ), hint), True)
                if self.forcing_chain_has_link(chain, loc):
                    hlmap[hint] = hlmap.get(hint, [])
                    hlmap[hint].append(loc)
        if not hlmap:
            return False
        if all([len(v) == 1 for k, v in hlmap.items()]):
            return False
        if self.test_purge(set(group), set([i])):
            locs = []
            for hint, l in hlmap.items():
                if len(l) > 1:
                    locs += l
            reason = self.nishio_info(chain, locs)
            self.purge_hints(plan, set(group), set([i]), reason, "lot multi hint")
            return True
        return False

    """
    Check for all occurrences of a hint in the lot with color False.
    """
    def nishio_lot_excl_hint(self, plan, origin, chain, lot):
        (group, i), color = origin
        hlmap = dict()
        blacklist = list()
        for node in lot.get_nodes():
            if node.is_complete():
                continue
            for hint in node.get_hints():
                if hint in blacklist:
                    continue
                loc = (((node, ), hint), True)
                if self.forcing_chain_has_link(chain, loc):
                    blacklist.append(hint)
                    if hint in hlmap:
                        hlmap.pop(hint)
                    continue
                loc = (((node, ), hint), False)
                if not self.forcing_chain_has_link(chain, loc):
                    blacklist.append(hint)
                    if hint in hlmap:
                        hlmap.pop(hint)
                    continue
                hlmap[hint] = hlmap.get(hint, [])
                hlmap[hint].append(loc)
        if not hlmap:
            return False
        if self.test_purge(set(group), set([i])):
            locs = []
            for hint, l in hlmap.items():
                locs += l
            reason = self.nishio_info(chain, locs)
            self.purge_hints(plan, set(group), set([i]), reason, "lot excl hint")
            return True
        return False

    """
    Return information regarding the nishio forcing chain.
    """
    def nishio_info(self, chain, locs):
        return {
            "chain": [self.forcing_chain_format(chain, x, False) for x in locs],
            "__chain__": [self.forcing_chain_find_path(chain, x) for x in locs],
            }

    """
    Process the forcing chain for various conflicting scenarios.
    """
    def nishio_process(self, plan, origin, chain):
        # Node based attacks.
        for node in plan.get_sudoku().get_incomplete():
            if self.nishio_node_multi_color(plan, origin, chain, node):
                return True
            if self.nishio_node_multi_hint(plan, origin, chain, node):
                return True
            if self.nishio_node_excl_hint(plan, origin, chain, node):
                return True

        # Lot based attacks.
        for lot in plan.get_sudoku().get_lots():
            if self.nishio_lot_multi_hint(plan, origin, chain, lot):
                return True
            if self.nishio_lot_excl_hint(plan, origin, chain, lot):
                return True

        return False

    """
    Construct the pair of digit forcing chains, one for each
    color, for each node and hint combination.
    """
    def nishio(self, plan, i):
        for node in plan.get_sudoku().get_incomplete():
            if not i in node.get_hints():
                continue
            chain = dict()
            origin = (((node, ), i), True)
            self.forcing_chain_walk(origin, chain)
            if self.nishio_process(plan, origin, chain):
                return True
        return False

    """
    Look for an process nishio forcing chain for all hints.
    """
    def run(self, plan):
        for i in range(1, 10):
            if self.nishio(plan, i):
                return True
        return False

class DigitForcingChain(ForcingChain):

    __metaclass__ = StrategyMeta

    def __init__(self):
        ForcingChain.__init__(self, "DIGIT FORCING-CHAIN", False, 2)

    """
    Check if the hint in the node is turned on in two paths
    one from each chain.
    """
    def digit_node_hint_true(self, plan, pair, node, hint):
        on, off = pair
        loc = (((node, ), hint), True)
        if all([self.forcing_chain_has_link(x, loc) for x in pair]):
            if self.test_update([node], set([hint])):
                reason = self.digit_info(on, [loc], off, [loc])
                self.update_hints(plan, [node], set([hint]), reason, "node hint true")
                return True
        return False

    """
    Check if the hint in the node is turned off in two paths
    one from each chain.
    """
    def digit_node_hint_false(self, plan, pair, node, hint):
        on, off = pair
        loc = (((node, ), hint), False)
        if all([self.forcing_chain_has_link(x, loc) for x in pair]):
            if self.test_purge([node], set([hint])):
                reason = self.digit_info(on, [loc], off, [loc])
                self.purge_hints(plan, [node], set([hint]), reason, "node hint false")
                return True
        return False

    """
    Check if multiple hints are turned on in two paths one from
    each chain.
    """
    def digit_node_multi_hint(self, plan, pair, node):
        if len(node.get_hints()) < 3:
            return False

        on, off = pair
        locs = set([(((node, ), h), True) for h in node.get_hints()])
        onlocs = set([x for x in locs if self.forcing_chain_has_link(on, x)])
        offlocs = set([x for x in locs if self.forcing_chain_has_link(off, x)])
        if onlocs and offlocs:
            locs -= onlocs | offlocs
            hints = set([h for (g, h), c in locs])
            if self.test_purge([node], hints):
                reason = self.digit_info(on, onlocs, off, offlocs)
                self.purge_hints(plan, [node], hints, reason, "node multi hint")
                return True

        return False

    """
    Check if the same hint in the lot is turned on in two paths
    one from each chain.
    """
    def digit_lot_hint_true(self, plan, pair, lot):
        on, off = pair
        onmap = dict()
        offmap = dict()
        for node in lot.get_nodes():
            if node.is_complete():
                continue
            for hint in node.get_hints():
                loc = (((node, ), hint), True)
                if self.forcing_chain_has_link(on, loc):
                    onmap[hint] = onmap.get(hint, [])
                    onmap[hint].append(loc)
                if self.forcing_chain_has_link(off, loc):
                    offmap[hint] = offmap.get(hint, [])
                    offmap[hint].append(loc)
        for hint, onlocs in onmap.items():
            if not hint in offmap:
                continue
            offlocs = offmap[hint]
            nodes = set([n for ((n, ), h), c in onlocs + offlocs])
            nodes = set(lot.get_nodes()) - nodes
            if self.test_purge(nodes, set([hint])):
                reason = self.digit_info(on, onlocs, off, offlocs)
                self.purge_hints(plan, nodes, set([hint]), reason, "lot hint true")
                return True
        return False

    """
    Return the information regarding the digit forcing chain.
    """
    def digit_info(self, on, onlocs, off, offlocs):
        return {
            "chain": [self.forcing_chain_format(on, loc, False) for loc in onlocs] +
            [self.forcing_chain_format(off, loc, False) for loc in offlocs],
            "__chain__": [self.forcing_chain_find_path(on, loc) for loc in onlocs] +
            [self.forcing_chain_find_path(off, loc) for loc in offlocs],
            }

    """
    Process the pair of digit forcing chains that originated
    from the given node and hint.
    """
    def digit_process(self, plan, pair):
        on, off = pair

        # Node based attacks.
        for node in plan.get_sudoku().get_incomplete():
            # Single hint attacks.
            for hint in node.get_hints():
                if self.digit_node_hint_true(plan, pair, node, hint):
                    return True
                if self.digit_node_hint_false(plan, pair, node, hint):
                    return True

            if self.digit_node_multi_hint(plan, pair, node):
                return True

        # Lot based attacks.
        for lot in plan.get_sudoku().get_lots():
            if self.digit_lot_hint_true(plan, pair, lot):
                return True

        return False

    """
    Construct the pair of digit forcing chains, one for each
    color, for each node and hint combination.
    """
    def digit(self, plan, i):
        for node in plan.get_sudoku().get_incomplete():
            if not i in node.get_hints():
                continue
            pair = []
            for color in [True, False]:
                chain = dict()
                origin = (((node, ), i), color)
                self.forcing_chain_walk(origin, chain)
                pair.append(chain)
            if self.digit_process(plan, pair):
                return True
        return False

    """
    Look for an process digit forcing chain for all hints.
    """
    def run(self, plan):
        for i in range(1, 10):
            if self.digit(plan, i):
                return True
        return False
