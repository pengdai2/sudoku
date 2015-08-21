#
# Sudoku playbook module.
#
# This module provides the Sudoku playbook which is essentially
# a collection Sudoku strategies. An abstract Sudoku strategy
# class is implemented here to serve as the base class for all
# Sudoku strategies. From the playbook, one can derive a plan
# of attack. The plan is a sorted list of strategies enabled by
# the user. The plan then iterates through the strategies to
# attack a particular Sudoku instance.
#

import abc
import json
from logger import *
from sudoku import *

class SudokuEncoder(json.JSONEncoder):

    """
    Extended JSON encoder for Sudoku support.
    """
    def default(self, obj):
        if isinstance(obj, Node):
            return obj.format()
        if isinstance(obj, Lot):
            return obj.format()
        if isinstance(obj, Sudoku):
            return obj.format()
        if isinstance(obj, Optional):
            return str(obj)

        return json.JSONEncoder.default(self, obj)

    """
    Format the given object into JSON message.
    """
    @staticmethod
    def format(obj, indent = None):
        return json.dumps(obj, indent = indent, cls = SudokuEncoder)

class Options(object):

    """
    Options for customizing Sudoku solution execution. Currently
    it supports the selection of strategies as well as hooks.
    """

    """
    Default strategy levels. Same leveled strategies are executed
    together even if a lower level strategy may progress.
    """
    DEFAULT_LEVELS = {
        # Level 0
        "SINGLETON" : 0,
        # Level 1
        "NAKED-GROUP" : 1,
        "INTERSECTION" : 1,
        "HIDDEN-GROUP" : 1,
        # Level 2
        "X-WING" : 2,
        "SIMPLE-COLORING" : 2,
        "XYZ-WING" : 2,
        "Y-WING" : 2,
        # Level >= 10
        "X-CYCLE" : 10,
        "XY-CHAIN" : 11,
        "3D-MEDUSA" : 12,
        "SWORD-FISH" : 13,
        "ALS" : 14,
        # Level >= 20
        "GROUPED-X-CYCLE" : 20,
        "UNIQUE-RECTANGLE" : 21,
        "WXYZ-WING" : 22,
        # Level >= 30
        "APE" : 30,
        "JELLY-FISH" : 31,
        # Level >= 40
        "FINNED X-WING" : 40,
        "FINNED SWORD-FISH" : 41,
        "AIC" : 42,
        # Level >= 50
        "DIGIT FORCING-CHAIN" : 50,
        "NISHIO FORCING-CHAIN" : 51,
        # Level >= 60
        "GROUPED-AIC" : 60,
        # Level > 90
        "TRIAL-1" : 97,
        "TRIAL-2" : 98,
        "TRIAL-3" : 99
        }

    def __init__(self):
        self.options = dict()
        self.levels = self.DEFAULT_LEVELS

    def copy(self):
        options = Options()
        options.options = dict(self.options)
        options.levels = dict(self.levels)
        return options

    def enabled(self, o):
        return self.options[o.get_name()] if o.get_name() in self.options else o.default()

    def enable(self, o):
        self.options[o.get_name()] = True

    def disable(self, o):
        self.options[o.get_name()] = False

    def get_level(self, s):
        return self.levels[s.get_name()] if s.get_name() in self.levels else 100

    def set_level(self, s, l):
        self.levels[s.get_name()] = l

    def __str__(self):
        return str(self.options)

class Plan(object):

    """
    The class represents a plan of attack. It is formulated by
    selecting the strategies from the playbook. It is responsible
    for the execution of the strategies in the specific order.
    It also supports extensible hooks.
    """
    def __init__(self, sudoku, options):
        self.sudoku = sudoku
        self.options = options

        self.strategies = dict()

        self.hooks = list()
        self.parms = dict()
        self.attrs = dict()

    def get_sudoku(self):
        return self.sudoku

    def get_options(self):
        return self.options

    def add_strategy(self, strategy, level):
        if strategy in self.all_strategies():
            return False
        self.strategies[level] = self.strategies.get(level, [])
        self.strategies[level].append(strategy)
        return True

    def del_strategy(self, strategy):
        for level in self.strategies:
            if strategy in self.strategies[level]:
                self.strategies[level].remove(strategy)
                return True
        return False

    def all_strategies(self):
        lsets = [set(x) for x in self.strategies.values()]
        return tuple(set.union(*lsets)) if lsets else tuple()

    def add_hook(self, hook):
        self.hooks.append(hook)

    def del_hook(self, hook):
        self.hooks.remove(hook)

    def all_hooks(self):
        return tuple(self.hooks)

    def set_attr(self, hook, attr):
        self.attrs[hook] = attr
    
    def get_attr(self, hook):
        return self.attrs.get(hook, None)

    def set_parm(self, hook, parm):
        self.parms[hook] = parm

    def get_parm(self, hook):
        return self.parms.get(hook, None)

    def iterate(self):
        for level in sorted(self.strategies.keys()):
            status = False
            for strategy in self.strategies[level]:
                if strategy.execute(self):
                    status = True
                    if self.done():
                        break
            if status:
                return True
        return False

    def done(self):
        if not self.sudoku.is_complete():
            return False
        self.sudoku.validate()
        return True

    def attack(self):
        while not self.done():
            if not self.iterate():
                Logger.debug(2, "impasse")
                return False
        Logger.debug(2, "success")
        return True

    def format(self):
        steps = [{"strategy": s, "level": l} for l in sorted(self.strategies.keys())
                 for s in self.strategies[l]]
        attrs = [{"hook": h, "data": d.format()} for h, d in self.attrs.items()]
        plan = {"steps": steps, "attrs": attrs}
        return SudokuEncoder.format(plan, indent = 4)

    def __str__(self):
        return self.format()

class Playbook(object):
    
    """
    A playbook is a static registry of all Sudoku strategies implemented.
    From the playbook, we can derive a specific plan of attack. The plan
    may be customized based on options specified. For example, certain
    strategies may be enabled or disabled.
    """

    catalog = dict()
    hooks = dict()
    default = Options()

    @staticmethod
    def register_strategy(strategy):
        Playbook.catalog[strategy.get_name()] = strategy

    @staticmethod
    def all_strategies():
        return tuple(Playbook.catalog.values())

    @staticmethod
    def register_hook(hook):
        Playbook.hooks[hook.get_name()] = hook

    @staticmethod
    def all_hooks(hook):
        return tuple(Playbook.hooks.values())

    @staticmethod
    def get_plan(sudoku, options = None):
        if options is None:
            options = Playbook.default.copy()
        plan = Plan(sudoku, options)
        for strategy in Playbook.catalog.values():
            if options.enabled(strategy):
                plan.add_strategy(strategy, options.get_level(strategy))
        for hook in Playbook.hooks.values():
            if options.enabled(hook):
                plan.add_hook(hook)
        return plan

    @staticmethod
    def show_info(header, info, trial):
        # We are only interested in the master plan.
        if not trial:
            print header + ":"
            print info

    @staticmethod
    def solve(sudoku, options = None, trial = False):
        Playbook.show_info("options", options, trial)
        plan = Playbook.get_plan(sudoku, options)
        Playbook.show_info("pre attack", plan, trial)
        try:
            status = plan.attack()
        finally:
            Playbook.show_info("post attack", plan, trial)
        return status

class Optional(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, name):
        self.name = name

    def get_name(self):
        return self.name

    """
    Return True if the default is enabled in the absence of explicit
    user setting.
    """
    @abc.abstractmethod
    def default(self):
        return NotImplemented

class HookMeta(abc.ABCMeta):

    """
    This is similar to StrategyMeta.
    """
    def __init__(cls, name, bases, dct):
        Playbook.register_hook(cls())

class Hook(Optional):

    """
    This is the base class for all strategy execution hooks.
    """
    def __init__(self, name):
        Optional.__init__(self, name)

    @abc.abstractmethod
    def pre_run(self, plan, strategy):
        return NotImplemented

    @abc.abstractmethod
    def post_run(self, plan, strategy, status):
        return NotImplemented

    @abc.abstractmethod
    def pre_update(self, plan, strategy, reason, action):
        return NotImplemented

    @abc.abstractmethod
    def post_update(self, plan, strategy, reason, action):
        return NotImplemented

    """
    See Optional.default(). By default a hook is disable. A
    specific hook may override.
    """
    def default(self):
        return False

    def __str__(self):
        return "HK.{0}".format(self.name)

class HookState(object):

    __metaclass__ = abc.ABCMeta

    """
    This is the base class for all hook states used by any
    stateful hooks. Each subclass must implement the format()
    method to return a JSON formattable object.
    """

    def __init__(self, hook):
        self.hook = hook

    @abc.abstractmethod
    def format(self):
        return NotImplemented

class StrategyMeta(abc.ABCMeta):

    """
    Metaclass that automatically registers the strategy with the playbook.
    This is done with a metaclass because in Python we cannot instantite
    an object of a class in the class definition.
    """
    def __init__(cls, name, bases, dct):
        Playbook.register_strategy(cls())

class Strategy(Optional):

    """
    Strategy base class. Each subclass defines a Sudoku strategy by
    filling out the run() method.
    """
    def __init__(self, name):
        Optional.__init__(self, name)
        self.last_reason = None

    """
    Strategy is by default repeatable.
    """
    def one_shot(self):
        return False

    """
    Return the set of nodes that are visible to any of the given
    seed nodes except the seed nodes themselves.
    """
    def find_related(self, nodes):
        return set.union(*[node.find_related() for node in nodes]) - set(nodes) if nodes else set()

    """
    Return the set of nodes that are visible to all of the given
    seed nodes except the seed nodes themselves.
    """
    def join_related(self, nodes):
        return set.intersection(*[node.find_related() for node in nodes]) - set(nodes) if nodes else set()

    """
    Return the set of hints from the given group of nodes.
    """
    def all_hints(self, nodes):
        return set.union(*[x.get_hints() for x in nodes]) if nodes else set()

    """
    Return the common set of hints from the given group of nodes.
    """
    def join_hints(self, nodes):
        return set.intersection(*[x.get_hints() for x in nodes]) if nodes else set()

    """
    Return the set of hints exclusive to the given nodes from row,
    column, or box.
    """
    def exclusive_hints(self, nodes):
        lots = set.intersection(*[set(x.get_lots()) for x in nodes])
        return set.union(*[x.exclusive_hints(nodes) for x in lots])

    """
    Check if purging the hints from the given nodes will lead to any
    effective changes.
    """
    def test_purge(self, nodes, hints):
        return any([node.get_hints() & hints for node in nodes if not node.is_complete()])

    """
    Purge the set of hints from the given nodes for the specified
    reason. Return True if the hints of any of the given nodes are
    modified.
    """
    def purge_hints(self, plan, nodes, hints, reason = None, note = None):
        status = False
        for node in nodes:
            if node.is_complete():
                continue
            if self.test_purge([node], hints):
                action = {
                    "node": node,
                    "remove": True,
                    "hints": sorted(hints),
                    "note": note
                    };
                if self.update_node(plan, node, node.get_hints() - hints, action, reason):
                    status = True
        return status

    """
    Check if updating the hints from the given nodes will lead to any
    effective changes.
    """
    def test_update(self, nodes, hints):
        return any([node.get_hints() - hints for node in nodes if not node.is_complete()])

    """
    Update the node with the given set of hints. Return True is the
    hints of any of the given nodes are modified.
    """
    def update_hints(self, plan, nodes, hints, reason = None, note = None):
        status = False
        for node in nodes:
            if node.is_complete():
                continue
            diff = node.get_hints() - hints
            if self.purge_hints(plan, [node], diff, reason, note):
                status = True
        return status

    """
    Refresh the node with the latest set of hints due to change of a
    related node. This is called once at the beginning across the
    board and then recursively when a node reaches completeness.
    """
    def refresh_node(self, plan, node):
        if node.is_complete():
            return False
        hints = set.intersection(*[x.get_missing_values() for x in node.get_lots()])
        if not hints:
            raise LogicException(node)
        if not node.has_hints():
            action = {
                "node": node,
                "remove": False,
                "hints": sorted(hints),
                "note": None
                };
            return self.update_node(plan, node, hints, action)
        else:
            return self.update_hints(plan, [node], hints)

    """
    Update the node with the given hints. Pre and post update hooks
    are always fired here so make sure the node hints will actually
    change before calling. If the node is completed, the related ones
    are recusively updated to ensure the board is consistent at all
    times.
    """
    def update_node(self, plan, node, hints, action, reason = None):
        # Avoid duplicate reasons.
        if reason:
            if reason is not self.last_reason:
                # Skip __raw__ info in the reason for JSON consumption.
                self.debug(3, dict((k, v) for k, v in reason.items()
                                   if not k.startswith("__") and not k.endswith("__")))
                self.last_reason = reason
            else:
                self.debug(3, "ditto... (multi-action)")

        self.debug(3, "node {0} => {1}".format(node, action));

        # Run pre update hooks.
        for hook in plan.all_hooks():
            if not hook.pre_update(plan, self, reason, action):
                return False

        node.update(hints)

        # Run post update hooks.
        for hook in plan.all_hooks():
            if not hook.post_update(plan, self, reason, action):
                return False

        # Update all related nodes once this node is complete.
        if node.is_complete():
            for x in node.find_related():
                self.refresh_node(plan, x)

        return True

    """
    Top level strategy entry point.
    """
    def execute(self, plan):
        # Pre run hooks.
        for hook in plan.all_hooks():
            if not hook.pre_run(plan, self):
                return False
        # Run the strategy.
        status = self.run(plan)
        # Post run hooks.
        for hook in plan.all_hooks():
            if not hook.post_run(plan, self, status):
                return False
        return status

    """
    Strategy entry point to be redefined in a subclass.
    """
    @abc.abstractmethod
    def run(self, plan):
        return NotImplemented

    """
    See Optional.default(). By default, a strategy is enabled. A
    specific strategy may override.
    """
    def default(self):
        return True

    """
    Convenience wrapper to append strategy name to a debug message.
    """
    def debug(self, level, message):
        Logger.debug(level, "{0}: {1}".format(self.name, message))

    def __str__(self):
        return "ST.{0}".format(self.name)
