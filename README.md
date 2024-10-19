# Transit | State Machines for TouchDesigner ⚡ powered by [transitions](https://github.com/pytransitions/transitions)

Transit is a COMP which wraps state machines written in the venerable [transitions](https://github.com/pytransitions/transitions) library and provides:

- Generated Params for monitoring state, triggering transitions and updating conditions
- Automatic association of states and OP settings, with smooth morphing, courtesy of [TDMorph](https://github.com/DarienBrito/TDMorph)

## Quickstart

1. Grab `transit.tox` from the releases and drop it into a project
2. Open `transit/TransitExt` in your favourite text editor. You'll see a simple default state machine defined in `__init__`. Replace that with one of your own design, referencing the [transitions docs](https://github.com/pytransitions/transitions). Here's how its features will be mapped to TouchDesigner:
    - The current state will get its own custom par which you can monitor in other OPs
    - Transition triggers will appear as pulses, including 'auto transitions' like `to_a`, `to_b`
    - Callbacks such as `conditions`, `before`, `after`, etc can reference methods you define on the extension by name. To enable this, set `model=self` on `Machine`.
  
For more on morphing, conditions and the API see further down.

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

## Caveats

- HierarchicalStateMachine is not yet supported
- Many transitions features are untested with this COMP. Make an issue/PR and I'll see if I can support them.

## Conditions

Use `self.transit.condition` to expose a float par on the COMP and make transitions conditional with it.

By default the condition will return True if the par is `>= 1`: `transitions=[..., {"trigger": "go", ..., "conditions": [self.transit.condition('is_valid')]`.

Pass a callback to create a more complex condition: `self.transit.condition('temperature', lambda t: t > 50)`.

## Morphing

On the `Transit` page you'll find these options:

- enable/disable preset storing when exiting a state
- enable/disable morphing to the preset for a state when entering it
- morph time
- target OPs

Set any OPs you want to target for morphing here, then try tweaking settings and triggering transitions. You should see your OP pars moving smoothly from state to state.

## Python API

- `op('transit').Map('a 1 b 2.7')`: a quick way to map the current state to a float. Returns `0` if the state isn't in your expr.
- `op('transit').Pick('a', ('b', 3.141), 'c')` same thing but slightly more typing :). Omit the value for a state to map it to its index in the args. So here `a` maps to 0, `c` maps to 2.
- `op('transit').IsState(state)` check if the current state matches `state`
