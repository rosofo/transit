from extUtils import CustomParHelper
import transitions
from itertools import product

class TransitionExt:

    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
        pass

    def GetConfig(self) -> 'transitions.core.TransitionConfig | list[transitions.core.TransitionConfig]':
        pass