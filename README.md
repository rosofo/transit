# Transit | State Machines for TouchDesigner ⚡ powered by [transitions](https://github.com/pytransitions/transitions)

Transit is a COMP which wraps state machines written in the venerable [transitions](https://github.com/pytransitions/transitions) library and provides:

- Generated Params for monitoring state, triggering transitions and updating conditions
- Automatic association of states and OP settings, with smooth morphing, courtesy of [TDMorph](https://github.com/DarienBrito/TDMorph)

## Quickstart

1. Grab `transit.tox` from the releases and drop it into a project
2. Edit `transit_callbacks` and replace the machine with your design, referencing the [transitions docs](https://github.com/pytransitions/transitions). You can optionally add fields and callbacks to the `Model` here for more complex behaviours
3. Set `Model Count` to the number of instances you want to track

### Outputs

- CHOP
  Represents the state of every model the machine is operating on
    - `state` channel: each sample is the current state of a model, represented as an index into the `states` attribute of the Machine
    - other channels: each sample is the state of a field you've defined on the model. Fields must be `int`, `float` or `bool` to appear.

### Inputs

- `in_events` CHOP:
  Dispatch events/triggers on a per-model basis
  - channel name: the name of the trigger
  - channel samples: the index of the model. For example with `Model Count` set to `1000`, the valid range for a sample is 0-999. Values outside the range are ignored.

- `in_event_data` CHOP:
  Extra data to provide with events. This will be passed to Machine callbacks as described in [passing data](https://github.com/pytransitions/transitions?tab=readme-ov-file#passing-data)

## Caveats

- HierarchicalStateMachine is not yet supported
