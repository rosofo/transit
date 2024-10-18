import re
from typing import Callable, Protocol

op("td_pip").PrepareModule("transitions")  # type: ignore
from transitions import Machine  # noqa: E402


class Extension(Protocol):
    ownerComp: "COMP"


class Transit:
    ext: Extension

    def __init__(self, extension: Extension) -> None:
        self.ext = extension
        self._reset_custom_pages()

    def _reset_custom_pages(self):
        comp = self.ext.ownerComp
        for page in comp.customPages:
            page.destroy()

    def condition(self, name: str, callback: Callable[[float], bool] | None = None):
        """Create a condition for use in transitions and expose it as a custom parameter"""
        comp = self.ext.ownerComp
        page = next((p for p in comp.customPages if p.name == "Conditions"), None)
        if page is None:
            page = comp.appendCustomPage("Conditions")

        par = next((p for p in page.pars if p.name == self.to_par_name(name)), None)
        if par is None:
            par = page.appendFloat(self.to_par_name(name), label=name)[0]

        if callback is not None:

            def callback_condition_fn(*args, **kwargs):
                return callback(par.eval())

            return callback_condition_fn
        else:

            def condition_fn(*args, **kwargs):
                return par.eval() >= 1

            return condition_fn

    def expose_machine(self, machine: Machine):
        """Expose states and events of a transitions.Machine as custom parameters"""
        comp = self.ext.ownerComp
        if not machine.name:
            raise ValueError("Machine must have a name")
        page_name = f"Machine:{machine.name.capitalize()}"
        page = comp.appendCustomPage(page_name)
        self._expose_state(machine, page)
        self._expose_events(machine, page)
        self._expose_presets(machine, page)

    def _expose_state(self, machine: Machine, page: "Page"):
        par = page.appendStr("State", label="State")
        par.readOnly = True
        par.val = machine.state

        def after_state_change(*args, **kwargs):
            par.val = machine.state

        machine.after_state_change.append(after_state_change)

    def _expose_events(self, machine: Machine, page: "Page"):
        for event in machine.events:
            debug(f"Exposing event {event}")
            par_name = self._event_par_name(event)

            def dispatch_event(self, *_, event=event):
                debug(f"Dispatching event {event}")
                machine.dispatch(event)

            self._create_pulse(
                page=page, callback=dispatch_event, par_name=par_name, label=event
            )

    def _expose_presets(self, machine: Machine, page: "Page"):
        page.appendSequence("Presets", label="Presets")  # type: ignore
        p = page.appendFloat("Presetvalue", label="Value")
        p.readOnly = True
        for state in machine.states:
            page.appendFloat(f"Preset{self.to_par_name(state).lower()}", label=state)
        page.owner.seq.Presets.blockSize = 1 + len(machine.states)

        machine.after_state_change.append(self._create_set_presets(machine))

    def _create_set_presets(self, machine: Machine):
        def set_presets(*args, **kwargs):
            comp = self.ext.ownerComp
            seq: "Sequence" = comp.seq.Presets
            state = machine.state
            for i, preset in enumerate(seq.blocks):
                matching_par = preset.parGroup[
                    f"Preset{self.to_par_name(state).lower()}"
                ][0]
                val = matching_par.eval()
                preset.par.Presetvalue.val = val

        return set_presets

    def _create_pulse(self, page: "Page", par_name, label, callback):
        page.appendPulse(par_name, label=label)

        method_name = f"onPar{par_name}"

        self._attach_ext_method(method_name, callback)

    def _attach_ext_method(self, method_name, method):
        method.__name__ = method_name

        setattr(self.ext.__class__, method_name, method)

    @staticmethod
    def _event_par_name(name: str):
        return "Dispatch" + Transit.to_par_name(name).lower()

    @staticmethod
    def to_par_name(name):
        return "".join([w for w in re.split(r"[\s_]+", name.capitalize())])
