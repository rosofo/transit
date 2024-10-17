import json
import pprint
import re
from typing import Any, Iterable
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

    def IsState(self, *states: str, exact: bool = False):
        self.State.val  # trigger dependency of the caller
        if exact:
            return all(self.is_state_exact(state) for state in states)
        else:
            return all(self.is_state_partial(state) for state in states)

    def OneOf(self, *states: str, exact: bool = False):
        return any(self.IsState(s, exact=exact) for s in states)

    def Pick(self, *states: str | tuple[str | Iterable[str], Any], exact: bool = False):
        for i, state in enumerate(states):
            value = i
            if isinstance(state, tuple):
                state, value = state
            state = (state,) if isinstance(state, str) else state
            if self.IsState(*state, exact=exact):
                return value
        return None

    def is_state_exact(self, state: str):
        return self.Machine.is_state(state, self.Machine)

    def is_state_partial(self, state: str):
        """Handle compound states. E.g. given state `a_b` or `[a, [b, c]]`, `is_state_partial('a') == True`."""
        # horrible but they can be arbitrarily nested!
        states_str = str(self.Machine.state)
        return state in states_str

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

    def Dispatch(self, event: str):
        return self.Machine.dispatch(event)

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
        self.SetState(initial)
        self.createCustomPars(config)

    def add_transition_from_op(self, name):
        t: "TransitionExt" = op(name)
        trans = t.GetConfig()
        debug("transition config: ", trans)
        self.Machine.add_transitions(trans)

    def after_state_change(self):
        debug("after state change", self.Machine.state)
        self.State.val = self.Machine.state

    def createCustomPars(self, config):
        transitions = config["transitions"]
        events = {t["trigger"] for t in transitions}
        page = next((p for p in self.ownerComp.pages if p.name == "Events"), None)
        if page is not None:
            page.destroy()
        page = self.ownerComp.appendCustomPage("Events")
        for event in events:
            par_name = "".join(event.capitalize().split("_"))
            page.appendPulse(par_name, label=event)
