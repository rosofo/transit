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
        in_ops: list["OP"] = [
            i.connections[0].owner
            for i in inlets
            if i.connections and i.connections[0].owner
        ]
        in_states = [op for op in in_ops if "stat_state" in op.tags]
        in_conds = [
            lambda: op.par.Valid.eval() == 1
            for op in in_ops
            if "stat_condition" in op.tags
        ]

        outlets = self.ownerComp.outputConnectors
        out_states = [
            conn.owner
            for i in outlets
            if i.connections and i.connections[0].owner
            for conn in i.connections
        ]
        event = self.evalEvent

        sources = [s.StateName for s in in_states]
        targets = [t.StateName for t in out_states]
        ts = []
        for target in targets:
            ts.append(
                {
                    "source": sources,
                    "dest": target,
                    "trigger": event,
                    "after": self.on_after,
                    "conditions": in_conds,
                }
            )
        return ts

    def on_after(self):
        op("trigger_after").par.triggerpulse.pulse()
        self.ownerComp.par.Transitioned.pulse()
