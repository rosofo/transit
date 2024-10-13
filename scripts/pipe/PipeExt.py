from extUtils import CustomParHelper
from transitions import Machine, Transition
from random import random


class PipeModel:
    inputs: list[COMP] = []
    outputs: list[COMP] = []
    machine: Machine

    def __init__(self) -> None:
        self.machine = Machine(self, states=["empty", "flowing"], initial="empty")
        self.machine.add_transition("flow", ["empty", "flowing"], "flowing")
        self.machine.add_transition("stop", "flowing", "empty")

    def on_enter_flowing(self, amount: float):
        debug("on_enter_flow", amount)
        op("constant1").par.const0value = amount
        if not self.outputs:
            return
        amount /= len(self.outputs)
        for output in self.outputs:
            output.flow(amount)

    def on_exit_flowing(self, _amount: float = 0):
        debug("on_exit_flow")
        op("constant1").par.const0value = 0

    def connect_output(self, comp: COMP):
        self.outputs.append(comp)


class PipeExt:
    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
        # using a separate model to avoid potential clashes with CustomParHelper
        self.Model = PipeModel()

        CustomParHelper.Init(
            self, ownerComp, enable_properties=True, enable_callbacks=True
        )
        # self.onParIn(self.evalIn, None, None)

    def onParFlow(self):
        self.Model.flow(random())

    def onParEmpty(self):
        self.Model.stop()

    def onParIn(self, comp: COMP, val: COMP, prev: Par):
        if comp is None:
            prev.Model.disconnect_output(self.Model)
            self.Model.inputs = [c for c in self.Model.inputs if c.name != comp.name]
            return
        self.Model.inputs.append(comp)
        comp.Model.connect_output(self.Model)

    def onParOut(self, comp: COMP):
        self.Model.output = comp
