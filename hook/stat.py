#
# Stat hook module
#
# This module is responsible for maintaining execution stats of
# strategies included in a plan. All hooks are stateless by
# design. But most hooks except for the most trivial needs to
# maintain some data during plan execution, such as this one.
# Hook data is stored in the plan as hook attribute.
#

import time
from logger import *
from playbook import *

class StatPiece(object):

    """
    Execution statistics of a given strategy, including success and
    failure counts as well as total elapsed time.
    """
    def __init__(self, strategy):
        self.strategy = strategy
        self.success = 0
        self.failure = 0
        self.elapsed = 0
        self.start = 0

    def start_run(self):
        Logger.debug(4, "{0}: commence".format(self.strategy))
        self.start = time.time()

    def stop_run(self):
        self.elapsed = int((time.time() - self.start) * 1000)
        self.start = 0

    def succeeded(self):
        Logger.debug(4, "{0}: advance".format(self.strategy))
        self.success += 1

    def failed(self):
        Logger.debug(4, "{0}: blocked".format(self.strategy))
        self.failure += 1

    def format(self):
        return {
            "strategy": self.strategy,
            "success": self.success,
            "failure": self.failure,
            "elapsed": self.elapsed
            }

    def __str__(self):
        return self.format()

class StatData(HookState):

    def __init__(self, hook):
        HookState.__init__(self, hook)
        self.path = list()
        self.data = dict()

    def add_strategy(self, strategy):
        self.path.append(strategy)

    def get_stat(self, strategy):
        stat = self.data.get(strategy, None)
        if not stat:
            stat = StatPiece(strategy)
            self.data[strategy] = stat
        return stat

    def format(self):
        return {"paths": self.path, "stats": [x.format() for x in self.data.values()]}

    def __str__(self):
        return self.format()

class Stat(Hook):

    __metaclass__ = HookMeta

    def __init__(self):
        Hook.__init__(self, "STAT")

    def pre_run(self, plan, strategy):
        attr = plan.get_attr(self)
        if not attr:
            attr = StatData(self)
            plan.set_attr(self, attr)
        stat = attr.get_stat(strategy)
        stat.start_run()
        return True

    def post_run(self, plan, strategy, status):
        attr = plan.get_attr(self)
        stat = attr.get_stat(strategy)
        if status:
            attr.add_strategy(strategy)
            stat.succeeded()
        else:
            stat.failed()
        stat.stop_run()
        return True

    def pre_update(self, plan, strategy, reason, action):
        return True

    def post_update(self, plan, strategy, reason, action):
        return True

    """
    Unlike other hooks, stat hook should be enabled by default.
    """
    def default(self):
        return True
