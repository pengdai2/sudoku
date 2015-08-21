#
# Alternating Inference Chain (AIC) Loop strategy module
#

from logger import *
from playbook import *
from sudoku import *
from chain import *

class Loop(Chain):

    """
    AIC is a directional loop of nodes. A link in AIC takes the following
    form.

      ((A, B, ...), hint)

    A node list is used to support group-based AIC. If the hint remains
    the same throughout the AIC, it is an X-Cycle, which contains only
    bi-location links between two nodes. Otherwise, it's a general AIC,
    including bi-value links within the same node.

    Each link is assigned a binary color. As the name suggests, the color
    of a link alternates in the AIC. If a link has color False, the next
    link should be True, which implies a strong connection exists between
    the two links such that !A => B; otherwise, it is a weak connection
    such that A => !B.

    A perfectly alternating AIC is referred to as a contiguous Nice Loop,
    which has an even number of nodes, such as,

      +A-B+C-D

    Discontiguous Nice Loops are further characterized by the number and
    type of the discontiguity. For example, here is an AIC with one
    discontiguity that consists of two consecutive strong connections.
    This is referred to as a Strong Nice Loop.

      -A+B-C+A

    Similarly, here is one with two consecutive weak connections, which
    is referred to as a Weak Nice Loop.

      +A-B+C-A

    We look for Nice Loops, both contiguous and discontiguous, as follows.

      1) Pick a node and set the color to False.
      2) Look for all strong connections from the above node.
      3) For each strong connection, set the color of the corresponding
        node to True and append the node to the chain.
      4) From each node behind the strong connection, look for all weak
        connections and set the color of the corresponding node behind
        the weak connection to False.
      5) Go back to step 2) and repeat.

    The termination conditions are:

      1) We are looking for a weak connection next and there is one back
        to the beginning, which leads to a contiguous Nice Loop.
      2) We are looking for a strong connection next. There happens to be
        a strong connection back to the beginning, which leads to a Strong
        discontiguous Nice Loop.
      3) We are look for a strong connection next. Nonetheless, there is
        a weak connection back to the beginning, which leads to a Weak
        discontiguous Nice Loop.
      4) None of the above and we have no viable next connections to work
        with, which leads to nothing.

    It can be shown that the above algorithm produces all available AIC's,
    i.e., without missing any; and some of the AICs may be equivalent.

    Using the same example for contiguous Nice Loops, we can see all four
    of the following may be produced by the algorithm, depending on where
    we start the search and the initial color. They are no different from
    each other.

      -A+B-C+D (starting from A)
      -C+D-A+B (starting from C)
      -B+A-D+C (starting from B)
      -D+C-B+A (starting from D)

    In fact, there are more equivalent ones even though they are not
    found by the algorithm, such as,

      +A-D+C-B (starting from A in reverse direction as -A+B-C+D)
      +B-C+D-A (starting from B in reserse direction as -B+A-D+C)
      +C-B+A-D
      +D-A+B-C
    
    Two contiguous Nice Loops are equivalent if one can reach the other
    via shifting, such as -A+B-C+D and +B-C+D-A; or the reverse of one,
    in both order and color, can reach the other via shifting, such as
    -A+B-C+D and -D+C-B+A.

    For Strong discontiguous Nice Loop, while the algorithm can find it,
    the starting position is limited to the node between the two strong
    connections. We can still produce two equivalent ones depending on
    which of the two strong connections is followed next. For example,

      -A+B-C+A (follow strong connection to B)
      -A+C-B+A (follow strong connection to C)

    For Weak discontiguous Nice Loop, while the algorithm can find it,
    the starting position is limited to the two nodes at the opposite
    ends of the pair of weak connections. For example,

      +A-B+C-A (starting from B)
      +A-C+B-A (starting from C)

    Note that in the weak case, we start from -B or -C. As we find the
    weak connection back to B from A, we prepend +A to the chain, to
    represent that weak connection.
    
    For two discontiguous loops to be equivalent, the head and tail must
    be identical, in terms of both node and color; and the rest must be
    equivalent after reversing.

    To recap, we always produce chains with even number of links. If the
    head and tail links are identical, the chain is discontiguous; else,
    it is contiguous. In the former case, if the first link has color
    True, it's weak; else it's strong.
    """
    def __init__(self, name, biloc_only = True, group_limit = 0, length_limit = 16):
        Chain.__init__(self, name, biloc_only, group_limit)
        self.length_limit = length_limit

    """
    Check if the AIC is contiguous, i.e., -A+B-C+D.
    """
    def loop_contig(self, cycle):
        # Check for duplicate links.
        links = self.chain_all_links(cycle)
        if len(links) != len(cycle):
            return False
        # Check for color alternating.
        on = self.chain_all_links(cycle, None, True, 1, 2)
        off = self.chain_all_links(cycle, None, False, 0, 2)
        return len(on) == len(off) and len(off) + len(on) == len(links)

    """
    Check if the AIC is strong discontiguous, i.e., -A+B-C+A.
    """
    def loop_strong(self, cycle):
        # Check for single discontiguity.
        links = self.chain_all_links(cycle)
        if len(links) + 1 != len(cycle):
            return False
        # Check for mid-section of the chain.
        if not self.loop_contig(self.chain_flip(cycle[1:-1])):
            return False
        # Check for head and tail match.
        head, hc = cycle[0]
        tail, tc = cycle[-1]
        return head == tail and not hc and tc

    """
    Check if the AIC is weak discontiguous, i.e., +A-B+C-A.
    """
    def loop_weak(self, cycle):
        # Check for single discontiguity.
        links = self.chain_all_links(cycle)
        if len(links) + 1 != len(cycle):
            return False
        # Check for mid-section of the chain.
        if not self.loop_contig(cycle[1:-1]):
            return False
        # Check for head and tail match.
        head, hc = cycle[0]
        tail, tc = cycle[-1]
        return head == tail and hc and not tc

    """
    Check if two contiguous chains are identical except for shifting.
    For example, -A+B-C+D and -C+D-A+B
    """
    def loop_duplicate_oneway(self, cycle, other):
        if not cycle[0] in other:
            return False
        index = other.index(cycle[0])
        return cycle == other[index:] + other[0:index]

    """
    Check if two contiguous chains are identical. In addition to
    shifting the original, also check that the flipped version is
    shift equivalent.
    """
    def loop_duplicate_contig(self, cycle, other):
        return self.loop_duplicate_oneway(cycle, other) or \
            self.loop_duplicate_oneway(self.chain_reverse_flip(cycle), other)

    """
    Check if two strong discontiguous chains are identical. The heads
    must be identical and the mid-section must be exactly flip.
    """
    def loop_duplicate_strong(self, cycle, other):
        return cycle[0] == other[0] and self.chain_reverse_flip(cycle[1:-1]) == other[1:-1]

    """
    Check if two weak discontiguous chains are identical. The heads
    must be identical and the mid-section must be exactly flip.
    """
    def loop_duplicate_weak(self, cycle, other):
        return cycle[0] == other[0] and self.chain_reverse_flip(cycle[1:-1]) == other[1:-1]

    """
    Test if two AIC cycles are identical.
    """
    def loop_duplicate(self, cycle, other):
        if len(cycle) != len(other):
            return False
        if self.loop_contig(cycle) and self.loop_contig(cycle):
            return self.loop_duplicate_contig(cycle, other)
        if self.loop_strong(cycle) and self.loop_strong(other):
            return self.loop_duplicate_strong(cycle, other)
        if self.loop_weak(cycle) and self.loop_weak(other):
            return self.loop_duplicate_weak(cycle, other)
        return False

    """
    Process the AIC for hint elimination.
    """
    def loop_process(self, plan, cycle):
        reason = {"__chain__": cycle, "chain": self.chain_format(cycle, False)}

        # Contiguous Nice Loops.
        if self.loop_contig(cycle):
            return self.loop_process_contig(plan, cycle, reason)

        # Discontiguous Nice Loops.
        (group, i), color = cycle[0]

        # The node harboring the discontiguity has to be a single node
        # even in the case of group support. That is because we only
        # look for group to land a strong link in case one doesn't exist
        # and the start point is a single node. In the case of strong
        # loop, the discontiguity is at the start node; whereas for weak
        # loop, the discontiguity has two weak links both incoming and
        # outgoing. So in either case, it cannot be a group.
        assert len(group) == 1

        node = group[0]
        if node.is_complete():
            return False

        if self.loop_strong(cycle):
            hints = node.get_hints() - set([i])
            note = "discontig strong"
        elif self.loop_weak(cycle):
            hints = set([i])
            note = "discontig weak"
        else:
            return False

        return self.purge_hints(plan, [node], hints, reason, note)

    """
    Purge all hints in the AIC with the given color.
    """
    def loop_purge_color(self, plan, cycle, color, reason):
        status = False
        for node in self.chain_all_groups(cycle):
            hints = self.chain_group_hints(cycle, node, color)
            if self.purge_hints(plan, node, hints, reason):
                status = True
        return status

    """
    Process contiguous AIC.
    """
    def loop_process_contig(self, plan, cycle, reason):
        # Check if a node has multiple hints of the same color.
        # Obviously, they cannot all be true at the same time in a
        # single node, wich implies all hints of the same color in
        # the AIC should all be eliminated.
        for group in self.chain_all_groups(cycle):
            for color in [True, False]:
                hints = self.chain_group_hints(cycle, group, color)
                if len(hints) < 2:
                    continue
                note = "same-color {0}".format(list(group))
                return self.loop_purge_color(plan, cycle, color, reason, note)

        status = False

        # Check if a node has both colors, in which case, other
        # uncolored hints in the same node can be eliminated.
        for group in self.chain_all_groups(cycle):
            hints = self.chain_group_hints(cycle, group)
            if len(hints) == 1:
                continue
            if self.test_update(group, hints):
                self.update_hints(plan, group, hints, reason, "dual-color")
                status = True

        # Check if a node off-chain can see a hint of both colors
        # in the AIC, in which case, the hint in that node can be
        # eliminated.
        for hint in self.chain_all_hints(cycle):
            off = self.chain_group_related([x for x, y in self.chain_all_links(cycle, hint, False, 0, 2)])
            on = self.chain_group_related([x for x, y in self.chain_all_links(cycle, hint, True, 1, 2)])
            intersect = on & off
            if self.test_purge(intersect, set([hint])):
                self.purge_hints(plan, intersect, set([hint]), reason, "off-chain")
                status = True

    """
    Recusive AIC walk. It looks for and constructs all AIC's starting
    from the head and following cycle path to the next link.
    """
    def loop_walk(self, cycle):
        head, color = cycle[0]
        next, color = cycle[-1]

        slinks, wlinks, glinks = self.chain_find_links(
            next, len(self.chain_group_links(cycle)))

        # Strong links are simultaneously weak links but not vice versa.
        # That is because !A => B, the strong link condition, implies
        # A => !B. Group links are always strong links. But we are not
        # including group links as weak links.
        wlinks |= slinks
        slinks |= glinks

        links = wlinks if color else slinks

        if len(cycle) > 2:
            # Discontiguous strong Nice Loop.
            if not color and head in slinks:
                return [cycle + [(head, not color)]]
            # Discontiguous weak Nice Loop.
            if not color and head in wlinks:
                return [[(next, not color)] + cycle]
            # Contiguous Nice Loop.
            if color and head in wlinks:
                return [cycle]

        cycles = list()

        # Stop if the length limit has been reached. The longer the AIC
        # is, the more timing consuming it is to build it, due to the
        # exponentially increasing possibilities with each link being
        # appended.
        if len(cycle) == self.length_limit:
            return cycles

        # Filter out duplicate links.
        links = set([x for x in links if not self.chain_link_conflict(x, cycle)])

        for link in links:
            batch = self.loop_walk(cycle + [(link, not color)])
            cycles.extend(batch)
        return cycles

    """
    Look for and process the AIC's starting from a single hint. Process
    the AIC's as we discover them and return as soon as some progress is
    made from a new batch found.
    """
    def loop(self, plan, i):
        all = list()
        for node in plan.get_sudoku().get_incomplete():
            if not i in node.get_hints():
                continue
            status = False
            cycles = self.loop_walk([(((node, ), i), False)])
            for cycle in cycles:
                if any([self.loop_duplicate(cycle, x) for x in all]):
                    continue
                all.append(cycle)
                if self.loop_process(plan, cycle):
                    status = True
            if status:
                return True
        return False

    """
    Alternating Inference Chain, or AIC, based strategy. X-Cycle, being a
    special case of the more generic AIC strategy, is also covered here.

    Note AIC is a very expensive operation with potential many many cycles.
    If we wait until we found all the cycles before we process them, we'd
    be running for a very very long time. Instead, we will return as soon
    as some, any, progress is made in hopes that it will enable the lower
    level strategies to make progress, which are much cheaper.
    """
    def run(self, plan):
        for i in range(1, 10):
            if self.loop(plan, i):
                return True
        return False

class XCycle(Loop):

    __metaclass__ = StrategyMeta
    
    def __init__(self):
        Loop.__init__(self, "X-CYCLE")

class GroupedXCycle(Loop):

    __metaclass__ = StrategyMeta
    
    def __init__(self):
        Loop.__init__(self, "GROUPED-X-CYCLE", True, 1)

class AIC(Loop):

    __metaclass__ = StrategyMeta

    def __init__(self):
        Loop.__init__(self, "AIC", False, 0)

class GroupedAIC(Loop):

    __metaclass__ = StrategyMeta

    def __init__(self):
        Loop.__init__(self, "GROUPED-AIC", False, 2)
