import json
import pprint
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
        self.State = tdu.Dependency(val="initial")
        self.Collect()

    def DebugDump(self):
        table = op("table_debug")
        table.clear()
        table.appendRow(["self.State", self.State.peekVal])
        table.appendRow(
            [
                "self.Machine.state",
                self.Machine.state,
            ]
        )

    def IsState(self, state: str):
        self.State.val  # trigger dependency of the caller
        return self.Machine.is_state(state, self.Machine)

    def onParCollect(self):
        self.Collect()

    def onParState(self, state):
        self.SetState(state)

    def SetState(self, state):
        self.Machine.set_state(state)
        self.State.val = state

    def onParDispatch(self):
        event = self.evalEvent  # type: ignore
        self.Machine.dispatch(event)

    def DumpSchema(self, config):
        text = op("text_debug")
        text.text = pprint.pformat(config, indent=4)

    def Collect(self):
        # preserve the current state if it still exists
        preserve = self.State.peekVal
        ops = op("opfind1").rows(val=True)
        debug("ops", ops)

        config = {
            "states": [],
            "transitions": [],
            "after_state_change": self.after_state_change,
        }

        initial = None
        for name, type in ops[1:]:
            type = type[1:-1]  # remove quotes
            if type == "stat_state":
                s: "StateExt" = op(name)
                state = s.GetConfig()
                if state is None:
                    continue

                if initial is None:
                    initial = name
                config["states"].append(state)
            elif type == "stat_transition":
                t: "TransitionExt" = op(name)
                transitions = t.GetConfig()
                if isinstance(transitions, list):
                    config["transitions"].extend(transitions)
                else:
                    config["transitions"].append(transitions)

        debug("Collected config: ", config)
        if self.evalShowschema:
            self.DumpSchema(config)
        self.Machine = HierarchicalMachine(**config)

        self.SetState(preserve if preserve != "initial" else initial)

    def add_transition_from_op(self, name):
        t: "TransitionExt" = op(name)
        trans = t.GetConfig()
        debug("transition config: ", trans)
        self.Machine.add_transitions(trans)

    def after_state_change(self):
        debug("after state change", self.Machine.state)
        self.State.val = self.Machine.state
