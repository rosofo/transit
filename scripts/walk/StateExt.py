import transitions
from extUtils import CustomParHelper
import TDFunctions as tdf


class StateExt:
    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
        CustomParHelper.Init(
            self, ownerComp, enable_properties=True, enable_callbacks=True
        )

    @property
    def StateName(self):
        parent_states = self.find_parent_states()
        # debug("parent states", parent_states)
        # multiple parents indicates that this OP represents different substates of different states
        # compromise: use the first parent state
        if len(parent_states) > 1:
            debug("using first parent state ", parent_states[0])
        if parent_states:
            parent = parent_states[0]
            return parent + "_" + self.ownerComp.name
        else:
            return self.ownerComp.name

    def onParMakeactive(self):
        self.ownerComp.parent().SetState(self.StateName)

    def find_parent_states(self) -> list[str]:
        return [
            c.owner.StateName
            for o in self.ownerComp.inputConnectors
            for c in o.connections
            if "stat_state" in c.owner.tags
        ]

    def find_substates(self) -> list[str]:
        outputs = self.ownerComp.outputConnectors
        return [
            c.owner.name
            for o in outputs
            for c in o.connections
            if "stat_state" in c.owner.tags
        ]

    def IsSubstate(self) -> bool:
        owner: "COMP" = self.ownerComp
        return any(
            "stat_state" in c.owner.tags
            for o in owner.inputConnectors
            for c in o.connections
        )

    def GetConfig(self) -> "transitions.core.StateConfig | None":
        if self.IsSubstate():
            return None
        name = self.ownerComp.name
        substates = self.find_substates()
        if substates:
            return {"name": name, "parallel": substates, "initial": substates[0]}
        else:
            return name
