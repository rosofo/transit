# Transit | State Machines for TouchDesigner ⚡ powered by [transitions](https://github.com/pytransitions/transitions)

Transit is a COMP which wraps state machines written in the venerable [transitions](https://github.com/pytransitions/transitions) library and provides:

- Generated Params for monitoring state, triggering transitions and updating conditions
- Automatic association of states and OP settings, with smooth morphing, courtesy of [TDMorph](https://github.com/DarienBrito/TDMorph)

## Example

Given the following Machine (placed inside the `transit/TransitExt` DAT):

```python
self.transit = Transit(self)
self.Machine = Machine(
    self,
    name="myco",
    states=["smooth", "chaotic"],
    initial="smooth",
    transitions=[["go", "smooth", "chaotic"], ["go", "chaotic", "smooth"]],
)
self.transit.expose_machine(self.Machine)
```

You get a COMP that can do this:

https://github.com/user-attachments/assets/7208f4ff-9f1e-415d-a2e6-917104a9d61c

