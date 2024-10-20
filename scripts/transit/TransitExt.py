import re
from typing import Any, Iterable
from extUtils import CustomParHelper

op("td_pip").PrepareModule("transitions")
from Transit import Transit  # noqa: E402


CallbacksExt = op.TDModules.op("TDCallbacksExt").module.CallbacksExt  # type: ignore


class TransitExt(CallbacksExt):
    ownerComp: "COMP"

    def __init__(self, ownerComp):
        super().__init__(ownerComp)
        self.ownerComp = ownerComp
        self.Setup()
        CustomParHelper.Init(
            self, ownerComp, enable_properties=True, enable_callbacks=True
        )

    def Setup(self):
        self.transit = Transit(self)
        machine, Model = self.DoCallback("initMachine")["returnValue"]
        self.Machine = machine
        self.transit.expose_machine(self.Machine, model_class=Model)

    def IsState(self, *states: str, exact: bool = False):
        self.ownerComp.par.State.val  # trigger dependency of the caller
        if exact:
            return all(self.is_state_exact(state) for state in states)
        else:
            return all(self.is_state_partial(state) for state in states)

    def OneOf(self, *states: str, exact: bool = False):
        return any(self.IsState(s, exact=exact) for s in states)

    def Map(self, expr: str):
        terms = re.split(r"\s+", expr)
        if len(terms) % 2 != 0:
            raise ValueError(
                "Expression must have an even number of terms, e.g. 'state_a 0 state_b 1'"
            )
        pairs = list(zip(terms[::2], terms[1::2]))
        pairs = [(state, float(value)) for state, value in pairs]
        return self.Pick(*pairs)

    def Pick(self, *states: str | tuple[str | Iterable[str], Any], exact: bool = False):
        for i, state in enumerate(states):
            value = i
            if isinstance(state, tuple):
                state, value = state
            state = (state,) if isinstance(state, str) else state
            if self.IsState(*state, exact=exact):
                return value
        return 0

    def is_state_exact(self, state: str):
        return self.Machine.is_state(state, self.Machine)

    def is_state_partial(self, state: str):
        """Handle compound states. E.g. given state `a_b` or `[a, [b, c]]`, `is_state_partial('a') == True`."""
        # horrible but they can be arbitrarily nested!
        states_str = str(self.Machine.model.state)
        return state in states_str
