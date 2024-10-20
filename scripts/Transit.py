from collections import defaultdict
import re
from typing import Any, Callable
import typing
from common_types import Extension
from par_merging import ParMerger
import numpy as np

op("td_pip").PrepareModule("transitions")  # type: ignore
from transitions import Machine  # noqa: E402


class DefaultModel:
    pass


class Transit:
    ext: Extension
    _machine: Machine | None = None
    model_class: type[Any] = DefaultModel
    _model_fields: list[str] | None = None

    def __init__(self, extension: Extension) -> None:
        self.ext = extension
        self.par_merger = ParMerger(self.ext)
        self.par_merger.cache_settings()
        self.par_merger.clear_pages(ignore=["Transit"])

    @property
    def model_fields(self) -> list[str]:
        if self._model_fields is None:
            self._model_fields = [
                name
                for name, type in typing.get_type_hints(self.model_class).items()
                if type in [int, float, bool]
            ]

        return self._model_fields

    def get_model_states(self, include_fields: bool):
        models = self.machine.models
        output = defaultdict(list)
        for model in models:
            fields = ["state"]
            if include_fields:
                fields += self.model_fields
            for field in fields:
                output[field].append(getattr(model, field))
        return output

    @property
    def machine(self) -> Machine:
        if self._machine is None:
            raise ValueError("Machine not set, call expose_machine first")
        return self._machine

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

    def expose_machine(self, machine: Machine, model_class: type[Any] = DefaultModel):
        """Expose states and events of a transitions.Machine as custom parameters"""
        self._machine = machine
        self.model_class = model_class

        comp = self.ext.ownerComp
        if not machine.name:
            raise ValueError("Machine must have a name")
        page_name = f"Machine:{machine.name.capitalize()}"
        page = comp.appendCustomPage(page_name)
        self._expose_state_par(machine, page)
        self._expose_events(machine, page)
        self._enable_model_count_par(machine)
        self.par_merger.restore_settings()
        self._expose_models_dep()

    def _enable_model_count_par(self, machine: Machine):
        model_class = self.model_class

        def onParModelcount(self, value):
            models = machine.models
            if len(models) < value:
                for _ in range(value - len(models)):
                    machine.add_model(model_class())
            elif len(models) > value:
                for _ in range(len(models) - value):
                    machine.remove_model(models[-1])

        onParModelcount(self.ext, self.ext.ownerComp.par.Modelcount.eval())

        self._attach_ext_method("onParModelcount", onParModelcount)

    def _expose_models_dep(self):
        models = self.machine.models
        dep = tdu.Dependency(val=models)
        self._attach_ext_property("Models", dep)

        def notify(*args, **kwargs):
            dep.val = self.machine.models
            dep.modified()

        self.machine.after_state_change.append(notify)

    def process_chop_events(self, eventsOp: "CHOP", contextDataOp: "CHOP"):
        context_data = contextDataOp.numpyArray()
        context_data = np.transpose(context_data)
        context_data_fields: list[str] = [chan.name for chan in contextDataOp.chans()]  # type: ignore

        models = self.machine.models

        exc = None
        for chan in eventsOp.chans():  # type: ignore
            chan: "Channel"
            event_name: str = chan.name

            for sample_idx, model_idx in enumerate(chan.vals):
                if sample_idx >= len(context_data):
                    event_data = {}
                else:
                    event_data = dict(
                        zip(context_data_fields, context_data[sample_idx])
                    )

                model_idx = int(model_idx)
                if model_idx < 0 or model_idx >= len(models):
                    continue
                model = models[model_idx]
                try:
                    model.trigger(event_name, **event_data)
                except AttributeError as e:
                    exc = e
                    break

        if exc is not None:
            raise exc

    def _expose_state_par(self, machine: Machine, page: "Page"):
        par = page.appendStr("State", label="State")
        par.readOnly = True
        self._update_state_par(machine)

        machine.after_state_change.append(
            lambda *args, **kwargs: self._update_state_par(machine)
        )

    def _update_state_par(self, machine: Machine):
        par = self.ext.ownerComp.par.State
        if len(machine.models) > 1:
            if par.val != "Multiple Models":
                par.val = "Multiple Models"  # type: ignore
        else:
            try:
                par.val = machine.model.state
            except Exception as e:
                debug(f"Error updating state par: {e}")

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

    def _create_pulse(self, page: "Page", par_name, label, callback):
        page.appendPulse(par_name, label=label)

        method_name = f"onPar{par_name}"

        self._attach_ext_method(method_name, callback)

    def _attach_ext_method(self, method_name, method):
        method.__name__ = method_name

        setattr(self.ext.__class__, method_name, method)

    def _attach_ext_property(self, prop_name, prop):
        setattr(self.ext.__class__, prop_name, prop)

    @staticmethod
    def _event_par_name(name: str):
        return "Dispatch" + Transit.to_par_name(name).lower()

    @staticmethod
    def to_par_name(name):
        return "".join([w for w in re.split(r"[\s_]+", name.capitalize())])
