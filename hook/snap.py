#
# Snap hook module
#
# Take a series of snapshots during the execution of the plan.
# The snapshots can be conditioned upon user provided predicate.
# For example, on a particular node or on a set of strategies.
# Matching is done via regex.
#

import re
from playbook import *

class Event(object):

    def __init__(self, strategy, reason, snap):
        self.strategy = strategy
        self.reason = reason
        self.snap = snap
        self.action = None

    def add_action(self, a):
        if self.action is None:
            self.action = []
        self.action.append(a)

    def format(self):
        return {
            "strategy": self.strategy,
            "action": self.action,
            "reason": self.reason,
            "snap": self.snap
            }

    def __str__(self):
        return self.format()

class History(HookState):

    def __init__(self, hook, sudoku):
        HookState.__init__(self, hook)
        self.sudoku = sudoku
        self.events = list()

    """
    Return the last event in the history if it matches the
    specified strategy and reason.
    """
    def find_event(self, strategy, reason):
        if self.events:
            event = self.events[-1]
            if event.reason is reason and event.strategy is strategy:
                return event
        return None

    """
    Record the specified action in the history. It may be part
    of an existing event or a new one.
    """
    def record_action(self, strategy, reason, action):
        event = self.find_event(strategy, reason)
        if not event:
            snap = self.sudoku.save()
            event = Event(strategy, reason, snap)
            self.events.append(event)
        if action:
            event.add_action(action)

    def format(self):
        return [x.format() for x in self.events];

    def __str__(self):
        return self.format()

class Snap(Hook):

    __metaclass__ = HookMeta

    def __init__(self):
        Hook.__init__(self, "SNAP")

    def pre_run(self, plan, strategy):
        return True

    def post_run(self, plan, strategy, status):
        if plan.get_sudoku().is_complete():
            self.snap(plan, strategy, "final", None)
        return True

    def pre_update(self, plan, strategy, reason, action):
        self.snap(plan, strategy, reason, action)
        return True

    def post_update(self, plan, strategy, reason, action):
        return True

    def snap(self, plan, strategy, reason, action):
        parm = plan.get_parm(self)
        if parm and not re.match(parm, strategy.get_name()):
            return True
        if strategy.get_name() == "SINGLETON" or not reason:
            return True
        # Skip all trial and error strategies.
        if strategy.get_name().startswith("TRIAL"):
            return True
        history = plan.get_attr(self)
        if not history:
            history = History(self, plan.get_sudoku())
            plan.set_attr(self, history)
        history.record_action(strategy, reason, action)

    """
    Enable the SNAP hook by default since the web based UI relies
    on the JSON output it generates.
    """
    def default(self):
        return True
