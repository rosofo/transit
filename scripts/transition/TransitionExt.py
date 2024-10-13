from extUtils import CustomParHelper
import transitions
from itertools import product


class TransitionExt:
    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
        CustomParHelper.Init(
            self, ownerComp, enable_properties=True, enable_callbacks=True
        )

    def GetConfig(
        self,
    ) -> "transitions.core.TransitionConfig | list[transitions.core.TransitionConfig]":
        inlets: "list[Connector]" = self.ownerComp.inputConnectors
        in_states: list["OP"] = [
            i.connections[0].owner
            for i in inlets
            if i.connections and i.connections[0].owner
        ]
        outlets = self.ownerComp.outputConnectors
        out_states = [
            i.connections[0].owner
            for i in outlets
            if i.connections and i.connections[0].owner
        ]
        event = self.evalEvent

        sources = [s.name for s in in_states]
        targets = [t.name for t in out_states]
        ts = []
        for source, target in product(sources, targets):
            ts.append(
                {
                    "source": source,
                    "dest": target,
                    "trigger": event,
                    "after": self.on_after,
                }
            )
        return ts

    def on_after(self):
        op("trigger_after").par.triggerpulse.pulse()
