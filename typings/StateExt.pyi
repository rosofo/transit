import transitions
from extUtils import CustomParHelper

class StateExt:

    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
        pass

    def onParMakeactive(self):
        pass

    def find_substates(self) -> list[str]:
        pass

    def is_substate(self) -> bool:
        pass

    def GetConfig(self) -> 'transitions.core.StateConfig | None':
        pass