#
# Step hook module
#
# Simple hook for step-wise execution.
#

from playbook import *

class Step(Hook):

    __metaclass__ = HookMeta

    def __init__(self):
        Hook.__init__(self, "STEP")

    def pre_run(self, plan, strategy):
        return True

    def post_run(self, plan, strategy, status):
        return True

    def pre_update(self, plan, strategy, reason, action):
        # Skip singleton related updates.
        if strategy.get_name() == "SINGLETON" or not reason:
            return True
        # Skip all trial and error strategies.
        if strategy.get_name().startswith("TRIAL"):
            return True
        # Skip if continue was requested.
        attr = plan.get_attr(self)
        if attr:
            return True
        while True:
            step = raw_input("[n|c|s|d]> ")
            if not step or step == "n":
                return True
            elif step == "c":
                plan.set_attr(self, True)
                return True
            elif step == "s":
                return False
            elif step == "d":
                print plan.get_sudoku().format(True)
                print plan.get_sudoku().save()
            else:
                print "Please enter n for next, c for continue, s for skip, d for display."

    def post_update(self, plan, strategy, reason, action):
        return True
