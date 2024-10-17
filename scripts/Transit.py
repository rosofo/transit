from typing import Protocol

op("td_pip").PrepareModule("transitions")  # type: ignore
from transitions import Machine  # noqa: E402


class Extension(Protocol):
    ownerComp: "COMP"


class Transit:
    ext: Extension

    def __init__(self, extension: Extension) -> None:
        self.ext = extension

    def expose_machine(self, machine: Machine):
        self.expose_events(machine)

    def expose_events(self, machine: Machine):
        comp = self.ext.ownerComp
        page = self._recreate_page(comp, "Events")
        for event in machine.events:
            debug(f"Exposing event {event}")
            par_name = self._custom_par_name(event)

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

    @staticmethod
    def _recreate_page(comp: "COMP", name: str):
        page = next(
            (p for p in comp.customPages if p.name.lower() == name.lower()), None
        )
        if page is not None:
            page.destroy()
        page = comp.appendCustomPage(name)
        return page

    @staticmethod
    def _custom_par_name(name: str):
        return "Dispatch" + "".join([w for w in name.lower().split("_")])
