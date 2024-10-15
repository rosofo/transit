import re
from extUtils import CustomParHelper
from transitions.extensions import HierarchicalMachine


class StatExt:
    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
        self.Machine = HierarchicalMachine()
        CustomParHelper.Init(
            self, ownerComp, enable_properties=True, enable_callbacks=True
        )
        self.State = tdu.Dependency(val=self.state)
        self.Collect()

    def DebugDump(self):
        table = op("table_debug")
        table.clear()
        table.appendRow(["self.state", self.state])
        table.appendRow(
            [
                "self.Machine.state",
                self.Machine.state,
            ]
        )

    @property
    def state(self):
        return self.Machine.state

    def onParCollect(self):
        self.Collect()

    def onParState(self, state):
        self.SetState(state)

    def SetState(self, state):
        self.Machine.set_state(state)
        self.State.val = state

    def onParDispatch(self):
        event = self.evalEvent
        self.Machine.dispatch(event)

    def Collect(self):
        # preserve the current state if it still exists
        preserve = self.state
        self.Machine = HierarchicalMachine(after_state_change=self.after_state_change)
        ops = op("opfind1").rows(val=True)
        debug("ops", ops)
        initial = None
        for name, type in ops[1:]:
            type = type[1:-1]  # remove quotes
            if type == "stat_state":
                debug("adding state from op", name)
                added = self.add_state_from_op(name)
                if added and initial is None:
                    initial = name
            elif type == "stat_transition":
                debug("adding transition from op", name)
                self.add_transition_from_op(name)

        self.SetState(preserve if preserve != "initial" else initial)

    def add_state_from_op(self, name):
        s: "StateExt" = op(name)
        state = s.GetConfig()
        debug("state config: ", state)
        if state is None:
            return False
        self.Machine.add_state(state)
        return True

    def add_transition_from_op(self, name):
        t: "TransitionExt" = op(name)
        trans = t.GetConfig()
        debug("transition config: ", trans)
        self.Machine.add_transitions(trans)

    def after_state_change(self):
        debug("after state change", self.state)
        self.State.val = self.state
