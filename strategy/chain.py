#
# Alternating Inference Chain base module
#

from logger import *
from playbook import *
from sudoku import *
from chain import *

class Chain(Strategy):

    """
    This class provides the base support for chaining. It is shared
    between various families of alternating inference chain based
    strategies, such as AIC based on nice loops and forcing chains
    based on paths between nodes.

    A chain link takes the following form.

      ((A, B, ...), hint)

    where (A, B, ...) is a node list used to support group-based links
    and hint is a possible value for the group.

    Each link is assigned a binary color. The link color alternates
    in the AIC. If a link has color False, the next link must be True,
    which implies a strong connection exists between the two links
    such that !A => B; otherwise, it is a weak connection such that
    A => !B.

    Therefore, at any location in the chain, we have a 2-tuple of
    link and color.

      (link, color)

    A chain is an ordered list of such 2-tuples.
    """
    def __init__(self, name, biloc_only = True, group_limit = 0):
        Strategy.__init__(self, name)
        self.biloc_only = biloc_only
        self.group_limit = group_limit

    """
    Return the strong and weak links emanating from the specified
    link. The result takes the form of a pair of sets in a tuple.
    A strong link between A and B is one that !A => B and a weak
    link A => !B. A bi-location link is one that connects two nodes
    with the same hint whereas a bi-value link connects two hints
    in the same node.
    """
    def chain_find_links(self, link, group_count = 0):
        group, i = link
        node = group[0]

        # For group node, value links must be from the shared lots
        # to ensure that the link is visible to the group as a
        # whole.
        lots = set.intersection(*[set(x.get_lots()) for x in group])

        # Gather the set of nodes connected to the link by the value i
        # in each lot to which the link belongs.
        nsets = [lot.value_links(node, i) - set(group) for lot in lots]

        # Separate the node sets into strong and weak sets. A strong
        # set is one that has only one node in it while weak has more.
        ssets = [x for x in nsets if len(x) == 1]
        wsets = [x for x in nsets if len(x) > 1]

        # Flat out the node sets into a set of nodes.
        snodes = set.union(*ssets) if ssets else set()
        wnodes = set.union(*wsets) if wsets else set()

        # Construct the chain links.
        slinks = set([((x, ), i) for x in snodes])
        wlinks = set([((x, ), i) for x in wnodes])

        # Construct a link to each remaining hint in the node.
        if not self.biloc_only and not self.chain_is_group_link(link):
            hints = node.get_hints() - set([i])
            vlinks = set([((node, ), j) for j in hints])
            if len(hints) > 1:
                wlinks |= vlinks
            else:
                slinks |= vlinks

        # Look for group links. Groups links are always strong links
        # since it includes all the weak links from a particular lot in
        # a single group. Group links are not treated as weak links as
        # strong node links. Also, group link can only originate from
        # node link.
        glinks = set()
        if group_count < self.group_limit and not self.chain_is_group_link(link):
            glinks |= self.chain_find_group_links(link, wsets)

        return (slinks, wlinks, glinks)

    """
    A group link forms a strong link to a collection of otherwise weak
    links. All nodes partaking in the group link must be from the same
    lot. Furthermore, to allow the group link to join the chain, it has
    to be

      1) from the same box
      2) aligned in the same row or col.

    Otherwise, we will not be able to make both an incoming and outgoing
    links to and from it.
    """
    def chain_find_group_links(self, link, wsets):
        glinks = set()

        # Check if the set of all weak links from one lot form a
        # group link. If so, the group link formed must be a strong
        # link since there are no more weak links elsewhere.
        for wset in wsets:
            assert len(wset) > 1
            # Check if the weak nodes all reside in the same box.
            if len(set([x.get_box() for x in wset])) > 1:
                continue
            # Check if the weak nodes are either row or col aligned.
            if len(set([x.get_row() for x in wset])) > 1 and \
                    len(set([x.get_col() for x in wset])) > 1:
                continue
            glinks.add((tuple(wset), link[1]))

        return glinks

    """
    Find the collective area covered by a list of groups. This is
    similar to find_related() except we are working with groups
    rather than nodes. The area covered by a group is the join
    of the areas seen by all nodes in the group.
    """
    def chain_group_related(self, groups):
        return set.union(*[self.join_related(x) for x in groups]) if groups else set()

    """
    Return True if the given chain link is a group link.
    """
    def chain_is_group_link(self, link):
        return len(link[0]) > 1

    """
    Return the set of group links in the chain optionally matching
    hint, color, and location.
    """
    def chain_group_links(self, chain, hint = None, color = None, first = 0, step = 1):
        return set([x for x in self.chain_all_links(chain, hint, color, first, step)
                    if self.chain_is_group_link(x)])

    """
    Return True if the given chain has group links in it.
    """
    def chain_has_group_links(self, chain):
        return bool(self.chain_group_links(chain))

    """
    Return True if the given link conflicts with at least another
    in the chain. Conflict implies hint matching _and_ node group
    overlap.
    """
    def chain_link_conflict(self, link, chain):
        return any([set(link[0]) & set(g) and link[1] == h
                    for g, h in self.chain_all_links(chain)])

    """
    Return the set of links in the chain optionally conditioned upon the
    starting position, step, and hint matching. Each link takes the form
    of a 2-tuple with node and hint.
    """
    def chain_all_links(self, chain, hint = None, color = None, first = 0, step = 1):
        return set([l for l, c in chain[first::step]
                    if (hint is None or l[1] == hint) and
                    (color is None or c == color)])

    """
    Return the set of groups in the chain.
    """
    def chain_all_groups(self, chain, hint = None, color = None, first = 0, step = 1):
        return set([x for x, h in self.chain_all_links(chain, hint, color, first, step)])

    """
    Return the set of nodes in the chain.
    """
    def chain_all_nodes(self, chain, hint = None, color = None, first = 0, step = 1):
        return set.union(*[set(x) for x in self.chain_all_groups(chain, hint, color, first, step)])

    """
    Return the set of hints in the chain.
    """
    def chain_all_hints(self, chain, color = None, first = 0, step = 1):
        return set([h for x, h in self.chain_all_links(chain, None, color, first, step)])

    """
    Return the set of hints in the node.
    """
    def chain_group_hints(self, chain, group, color = None):
        return set([h for x, h in self.chain_all_links(chain, None, color) if x == group])

    """
    Return a new link in the chain that is identical to the given
    one except with its color flipped.
    """
    def chain_flip_link(self, loc):
        link, color = loc
        return (link, not color)

    """
    Return a new link in the chain that is identical to the given
    one except with its color changed.
    """
    def chain_link_set_color(self, loc, color):
        link, c = loc
        return (link, color)

    """
    Return a new chain with the color in each link flipped.
    """
    def chain_flip(self, chain):
        return [self.chain_flip_link(x) for x in chain]

    """
    Return a new chain that is a reverse of the one given with the
    color in each link flipped.
    """
    def chain_reverse_flip(self, chain):
        copy = []
        for x in chain:
            copy.insert(0, self.chain_flip_link(x))
        return copy


    """
    Format the chain for printing.
    """
    def chain_format(self, chain, verbose = True):
        return "".join("{0}{1}[{2}]".format(
                "+" if c else "-", h, "|".join(n.format(verbose) for n in g))
                       for (g, h), c in chain)
