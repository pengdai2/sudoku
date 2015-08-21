#
# Sudoku object module.
#
# This module contains various Sudoku entities such as node,
# row, col, box, and last but not the least the entire board.
# The strategy logic is teased out of this module entirely.
#

import re
import abc

class ValueException(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class LogicException(Exception):

    def __init__(self, entity):
        self.entity = entity

    def __str__(self):
        return repr(self.entity)

class Node(object):

    def __init__(self, value):
        self.check_value(value, True)

        self.value = value
        if value > 0:
            self.preset = True
        else:
            self.preset = False

        self.row = None
        self.col = None
        self.box = None

        self.hints = None

    def check_value(self, value, zero = False):
        if value < 0 or value > 9:
            raise ValueException(value)
        if not zero and value == 0:
            raise ValueException(value)

    def get_row(self):
        return self.row

    def set_row(self, row):
        self.row = row

    def get_col(self):
        return self.col

    def set_col(self, col):
        self.col = col

    def get_box(self):
        return self.box

    def set_box(self, box):
        self.box = box

    def get_lots(self):
        return (self.row, self.col, self.box)

    def at(self, i, j):
        return self.row.get_ident() == i and self.col.get_ident() == j

    def is_preset(self):
        return self.preset

    def is_complete(self):
        return self.value != 0

    def get_value(self):
        return self.value

    def has_value(self, value):
        return self.is_complete() and self.value == value

    def set_value(self, value):
        self.check_value(value)
        self.value = value
        self.reset_hints()

    def has_hints(self):
        return not self.hints is None

    def has_hint(self, hint):
        return hint in self.hints if self.has_hints() else False

    def get_hints(self):
        return self.hints.copy() if self.has_hints() else None

    def set_hints(self, hints):
        copy = set(hints)

        if self.has_hints():
            copy &= self.hints
            if copy == self.hints:
                return False

        self.hints = copy
        return True

    def reset_hints(self):
        self.hints = None

    """
    Return the set of all nodes related to this one.
    """
    def find_related(self):
        nodes = set(self.get_row().get_nodes())
        nodes |= set(self.get_col().get_nodes())
        nodes |= set(self.get_box().get_nodes())
        return nodes

    """
    Check if the given node is related to this one.
    """
    def is_related(self, node):
        return self.get_row() == node.get_row() or \
            self.get_col() == node.get_col() or \
            self.get_box() == node.get_box()

    """
    Update the hints on the node. Return True if hints have been changed.
    Note that the hints can only ever be eliminated over time.
    """
    def update(self, hints):
        # Through various strategies we may have eliminated certain hints
        # from the current set. On the other hand, the new hints may have
        # been derived from the containing lot, in which case, they may
        # include values that have been elimineated. We must not undo all
        # that work.
        if self.has_hints():
            hints &= self.get_hints()

        # There must exist at least one hint in a valid sudoku instance.
        if not hints:
            raise LogicException(self)

        # Bail out if there are multiple hints at this point.
        if len(hints) > 1:
            return self.set_hints(hints)

        # The node is resolved if there is but a single hint.
        self.set_value(hints.pop())

        return True

    def format(self, verbose = False, value = False):
        if value:
            return ("<{0}>" if self.is_preset() else " {0} ").format(self.value)
        if not verbose:
            return "{0}{1}".format(self.get_row(), self.get_col())
        value = sorted(self.hints) if self.has_hints() else self.value
        return "{0}{1}={2}".format(self.get_row(), self.get_col(), value)

    def __str__(self):
        return self.format(verbose = True)

    def __repr__(self):
        return self.__str__()

class Lot(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, sudoku, ident):
        self.sudoku = sudoku
        self.ident = ident
        self.nodes = None

    def get_sudoku(self):
        return self.sudoku

    def get_ident(self):
        return self.ident

    def get_nodes(self):
        return tuple(self.nodes)

    def get_node(self, i):
        return self.nodes[i]

    def count_incomplete(self):
        return len(self.get_incomplete())

    def is_complete(self):
        return not self.get_incomplete()

    def get_incomplete(self):
        return [node for node in self.nodes if not node.is_complete()]

    def has_value(self, value):
        return value in self.get_values()

    def get_values(self):
        return set([node.get_value() for node in self.nodes if node.is_complete()])

    def get_missing_values(self):
        return set(range(1, 10)) - self.get_values()

    def validate(self):
        values = self.get_values()
        if len(values) > len(set(values)):
            raise LogicException(self)

    """
    Return the set of hints from the given group of nodes.
    """
    def all_hints(self, nodes):
        return set.union(*[x.get_hints() for x in nodes]) if nodes else set()

    """
    Return the set of hints exclusive to the given nodes.
    """
    def exclusive_hints(self, nodes):
        return self.all_hints(nodes) - self.all_hints(self.other_nodes(nodes))

    """
    Return the set of incomplete nodes in the lot other than
    those given.
    """
    def other_nodes(self, nodes):
        return set(self.get_incomplete()) - set(nodes)

    """
    Return the set of incomplete nodes in the lot that are
    linked to the specified node by the given hint.
    """
    def value_links(self, node, i):
        return set([x for x in self.other_nodes([node]) if x.has_hint(i)])

    """
    Return the incomplete node in the lot that is exclusively
    linked to the specified node by the given hint.
    """
    def exclusive_link(self, node, i):
        links = self.value_links(node, i)
        return links.pop() if len(links) == 1 else None

class Row(Lot):

    def __init__(self, sudoku, nodes, ident):
        Lot.__init__(self, sudoku, ident)

        self.nodes = list(nodes[ident])

        for node in self.nodes:
            node.set_row(self)

        self.validate()

    def format(self, verbose = False):
        row = "ABCDEFGHJ"[self.get_ident()]
        if not verbose:
            return row
        return "{0}: {1}".format(row, " | ".join(node.format(verbose = True) for node in self.nodes))

    def __str__(self):
        return self.format()

    def __repr__(self):
        return self.__str__()

class Col(Lot):

    def __init__(self, sudoku, nodes, ident):
        Lot.__init__(self, sudoku, ident)

        self.nodes = []
        for row in nodes:
            self.nodes.append(row[ident])

        for node in self.nodes:
            node.set_col(self)

        self.validate()

    def format(self, verbose = False):
        col = str(self.get_ident() + 1)
        if not verbose:
            return col
        return "{0}: {1}".format(col, " | ".join(node.format(verbose = True) for node in self.nodes))

    def __str__(self):
        return self.format()

    def __repr__(self):
        return self.__str__()

class Box(Lot):

    def __init__(self, sudoku, nodes, ident):
        Lot.__init__(self, sudoku, ident)

        self.nodes = []
        row = (ident / 3) * 3
        col = (ident % 3) * 3
        for i in range(row, row + 3):
            self.nodes.extend(nodes[i][col : col + 3])

        for node in self.nodes:
            node.set_box(self)

        self.validate()

    def format(self, verbose = False):
        box = "abcdefghj"[self.get_ident()]
        if not verbose:
            return box
        return "{0}: {1}".format(box, " | ".join(node.format(verbose = True) for node in self.nodes))

    def __str__(self):
        return self.format()

    def __repr__(self):
        return self.__str__()

class Sudoku(object):

    def __init__(self, nodes, ident):
        self.ident = ident
        self.setup(nodes)

    def setup(self, nodes):
        self.nodes = nodes

        # Create rows.
        self.rows = []
        for ident in range(9):
            row = Row(self, nodes, ident)
            self.rows.append(row)

        # Create cols.
        self.cols = []
        for ident in range(9):
            col = Col(self, nodes, ident)
            self.cols.append(col)
            
        # Create boxes.
        self.boxes = []
        for ident in range(9):
            box = Box(self, nodes, ident)
            self.boxes.append(box)

        self.lots = self.rows + self.cols + self.boxes

    """
    Taks a snapshot of the Sudoku instance and return it.
    """
    def snap(self):
        grid = [[Node(node.get_value()) for node in row] for row in self.nodes]
        return Sudoku(grid, self.get_ident())

    """
    Copy the given Sudoku instance to this one.
    """
    def copy(self, sudoku):
        self.setup(sudoku.nodes)

    """
    Return an externalized string that represents this Sudoku instance.
    The string takes the format of a linear list of nodes 81 in total
    corresponding to the 9x9 configuration. Each node is represented by
    a number from 1 to 9 if it is complete, or 0 if not, or a list of
    bracketed and comma separated hints if so desired. For example,
    4598[1,2,3]7[6,1][2,6][1,3]
    """
    def save(self, hints = True):
        text = ""
        for i in range(9):
            for j in range(9):
                node = self.get_node(i, j)
                if node.is_complete():
                    x = str(node.get_value())
                elif hints:
                    x = str(sorted(node.get_hints()));
                    x = x.replace(" ", "")
                else:
                    x = str(0)
                text = text + x
        return text

    """
    Load the Sudoku instance from the given text and ident. The text
    is expected to be in the same format as described in the save()
    method.
    """
    @staticmethod
    def load(text, ident):
        items = re.findall("\d|\[[1-9](?:\s*,\s*[1-9]){1,8}\]", text)
        if len(items) != 81:
            raise ValueException(items)
        nodes = []
        for i in range(9):
            nodes.append([])
            for j in range(9):
                item = items[i * 9 + j]
                if item.startswith("["):
                    node = Node(0)
                    hints = set([int(h) for h in re.findall("\d", item)])
                    node.set_hints(hints)
                else:
                    node = Node(int(item))
                nodes[i].append(node)
        return Sudoku(nodes, ident)

    def get_ident(self):
        return self.ident

    def get_node(self, i, j):
        return self.nodes[i][j]

    def get_row(self, i):
        return self.rows[i]

    def get_col(self, j):
        return self.cols[j]

    def get_box(self, k):
        return self.boxes[k]

    def get_rows(self):
        return self.rows

    def get_cols(self):
        return self.cols

    def get_boxes(self):
        return self.boxes

    def get_lots(self):
        return self.lots

    def get_incomplete(self):
        return [node for row in self.nodes for node in row if not node.is_complete()]

    def count_incomplete(self):
        return len(self.get_incomplete())

    def is_complete(self):
        return not self.get_incomplete()

    def validate(self):
        for lot in self.lots:
            lot.validate()

    def format(self, pretty = False, verbose = False):
        if pretty:
            rs = "+---" * 9 + "+\n"
            cs = "|"
            rows = []
            for row in self.nodes:
                line = cs + cs.join(node.format(value = True) for node in row) + cs
                line = line + "\n"
                rows.append(line)
            diagram = rs + rs.join(rows) + rs
        elif verbose:
            sep = "\n------------------------\n"
            rows = "\n".join(row.format() for row in self.rows)
            cols = "\n".join(col.format() for col in self.cols)
            boxes = "\n".join(box.format() for box in self.boxes)
            diagram = sep.join([rows, cols, boxes])
        else:
            diagram = self.save()
        return diagram.strip()

    def __str__(self):
        return self.format()

    def __repr__(self):
        return self.__str__()
