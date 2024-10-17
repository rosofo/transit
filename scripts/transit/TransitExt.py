from extUtils import CustomParHelper
from Transit import Transit

op("td_pip").PrepareModule("transitions")
from transitions import Machine  # noqa: E402


class TransitExt:
    ownerComp: "COMP"

    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
        self.transit = Transit(self)
        self.Machine = Machine(
            states=["A", "B", "C"],
            initial="A",
            transitions=[{"trigger": "go", "source": "A", "dest": "B"}],
        )
        self.transit.expose_machine(self.Machine)
        CustomParHelper.Init(
            self, ownerComp, enable_properties=True, enable_callbacks=True
        )
