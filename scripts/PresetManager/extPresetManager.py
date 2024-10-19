"""
    TDMorph
    ========

    Copyright (c) 2020-2024 Darien Brito
    info@darienbrito.com
    https://www.darienbrito.com

    This file is part of TDMorph.

TDMorph is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

TDMorph is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with TDMorph. If not, see <https://www.gnu.org/licenses/>.
"""

from TDStoreTools import StorageManager
import re
import json
import itertools
import sys


class extPresetManager:
    """
    extPresetManager is the heart of TDMorph. This class is in charge
    of executing and manage all presets storage and retrieval as well
    as communicating with the morpher and random distribution nodes.

    #____ ARCHITECTURE ____#

    This operator works with paths to operators. This means that it
    addressses directly parameters, not sliders. Hence, it is totally
    independent from a UI. The design is aimed to be as close as possible
    to a Model View Controller (MVC) architecture, so one may thing of this
    class as a kind of Model.

    #____ EXTENDING ____#

    I strongly encourage you to maintain this philosophy if you want to
    expand this classes functionalities. This means keeping your UI "dumb"
    in the sense that the core operations of this object should ABSOLUTELY
    NOT depend on anything else to function.

    Since this project is both a toolkit and a set of UIs, there is another
    extension devoted exclusively to deal with UI calls named "extUIExtension".
    If you are in need to create some method that depends on a UI, you should
    use that class.
    """

    def __init__(self, ownerComp):
        # The component to which this extension is attached
        self.ownerComp = ownerComp

        storedItems = [
            {"name": "Presets", "property": True, "default": {}, "dependable": True},
            {"name": "AutoMode", "default": False, "property": True},
        ]

        self.stored = StorageManager(self, ownerComp, storedItems)

    # _____________ Properties ____________#

    @property
    def CurrentPresetName(self):
        self.ownerComp.par.Currentpreset
        return

    @CurrentPresetName.setter
    def CurrentPresetName(self, val):
        self.ownerComp.par.Currentpreset = val

    @property
    def CurrentMorphCounter(self):
        return self.ownerComp.par.Currentmorphcount

    @CurrentMorphCounter.setter
    def CurrentMorphCounter(self, val):
        self.ownerComp.par.Currentmorphcount = val

    @property
    def LoopSequenceStatus(self):
        return self.ownerComp.par.Loopsequence.eval()

    @LoopSequenceStatus.setter
    def LoopSequenceStatus(self, val):
        self.ownerComp.par.LoopSequence = val

    # ____ GETTERS/SETTERS WRAPPERS ____#

    @property
    def RandomDistribution(self):
        return op("PresetMorpher").RandomDistribution

    @RandomDistribution.setter
    def RandomDistribution(self, v):
        op("PresetMorpher").RandomDistribution = v

    @property
    def NumMorphs(self):
        return op("PresetMorpher").NumMorphs

    @NumMorphs.setter
    def NumMorphs(self, v):
        op("PresetMorpher").NumMorphs = v - 1

    @property
    def MorphTime(self):
        return op("PresetMorpher").MorphTime

    @MorphTime.setter
    def MorphTime(self, v):
        op("PresetMorpher").MorphTime = v

    @property
    def MorphCurve(self):
        return op("PresetMorpher").MorphCurve

    @MorphCurve.setter
    def MorphCurve(self, v):
        op("PresetMorpher").MorphCurve = v

    @property
    def ActivityStatus(self):
        return op("PresetMorpher").ActivityStatus

    @property
    def MorphingType(self):
        return op("PresetMorpher").MorphingType

    @property
    def Blend(self):
        return self.ownerComp.par.Blendfactor.eval()
        # return op('PresetMorpher').Blend

    @Blend.setter
    def Blend(self, v):
        self.ownerComp.par.Blendfactor = v

    @property
    def BlendingActive(self):
        return op("PresetMorpher").BlendingActive

    @BlendingActive.setter
    def BlendingActive(self, v):
        op("PresetMorpher").BlendingActive = v
        return

    @property
    def Lock(self):
        return bool(self.ownerComp.par.Lock)

    @Lock.setter
    def Lock(self, v):
        self.ownerComp.par.Lock = v
        return

    # _____________ Private ____________#

    def updatePresetsMenu(self):
        k = self.GetPresetsKeys()
        self.ownerComp.par.Target.menuNames = k
        self.ownerComp.par.Target.menuLabels = k
        return

    def parseSelection(self, op, data):
        """
        Parsing of user input in relation to what parameters
        to grab from targeted operators
        """
        builtIn = data["builtin"]
        custom = data["custom"]
        mode = "CUSTOM"

        if builtIn and not custom:
            mode = "BUILTIN"
        elif not builtIn and custom:
            mode = "CUSTOM"
        elif builtIn and custom:
            mode = "ALL"
        else:
            mode = "NONE"
        return mode

    def getParameterSelection(self, target, sel, scope):
        """
        Parse parameters to return based on pattern matching from
        the selected flags in the node. Wildcard matching is addressed
        via regular expressions, which provides a more comprehensive
        way to select targets.
        """
        params = None
        if sel == "CUSTOM":
            params = target.customPars
        elif sel == "BUILTIN":
            params = target.builtinPars
        elif sel == "ALL":
            params = target.builtinPars + target.customPars

        if params:
            params = [p for p in params if re.search(scope, p.name)]
        else:
            self.ReportResult(
                "No {} parameters found in {}." " Maybe you meant built-in?".format(
                    sel.lower(), target.name
                ),
                "Presets Manager",
            )

        return params

    def getParameterValue(self, par):
        """
        Grabs the source value based on certain conditions.
        There are some parameters, such as menu, that may
        require special treatment. This method is meant to
        handle that.
        """
        value = par.eval()
        # Check special cases: Menu, Toggle
        if par.style == "Menu":
            value = par.menuIndex
        elif par.style == "Toggle":
            value = int(par.eval())
        return value

    def getLockFromUI(self, path):
        # Check if there's an embedded UI to get locked status from,
        # otherwise grab the status from self.
        lockedSource = op(path).op("PresetManager")
        if lockedSource:
            return bool(lockedSource.Lock)
        else:
            return bool(self.Lock)

    def getParams(self, op, data):
        """
        Get the parameters current state. Takes useful information
        for morphing and parametric setting. We include here curve
        and time information.
        """
        if op is None:
            print("No target has been provided. Have you passed a path?")
            return None

        sel = self.parseSelection(op, data)
        pars = self.getParameterSelection(op, sel, data["filter"])
        return pars

    def getEsssentialStateFrom(self, op, data):
        """
        Grabs only essential elements to interpolate across tables.
        This reduces the amount of data to process per morph call.
        """
        # pars 	= [getattr(op.par, data[k]['paramName']) for k in data]

        state = []
        for d in data:
            name = d["paramName"]
            p = getattr(op.par, name)
            state.append(
                {
                    "paramName": p.name,
                    "value": self.getParameterValue(p),
                    "type": p.style,
                    "locked": self.getLockFromUI(p.owner.path),
                }
            )
        return state

    def getEsssentialState(self, op, data):
        """
        Grabs only essential elements to interpolate across tables.
        This reduces the amount of data to process per morph call.
        """
        pars = self.getParams(op, data)
        state = None
        if pars:
            state = []
            for p in pars:
                state.append(
                    {
                        "paramName": p.name,
                        "value": self.getParameterValue(p),
                        "type": p.style,
                        "locked": self.getLockFromUI(p.owner.path),
                    }
                )
        return state

    def getState(self, op, data):
        """
        Returns a list with the current state of parameters
        in the targeted operator.
        """
        pars = self.getParams(op, data)
        state = None
        if pars:
            state = []
            for p in pars:
                state.append(
                    {
                        "paramName": p.name,
                        "value": self.getParameterValue(p),
                        "type": p.style,
                        "normMin": p.normMin,
                        "normMax": p.normMax,
                        "min": p.min,
                        "max": p.max,
                        "locked": self.getLockFromUI(p.owner.path),
                    }
                )
        return state

    # _____________ Overwrite methods ____________#

    def OverwriteSinglePresetValue(self, name, item, val):
        """
        Used to overwrite a specific preset's value.
        Will overwrite the value for all parameters in that preset.
        """
        preset = self.Presets.get(name, None)
        if preset is None:
            self.ReportResult(
                "Could not overwrite. Preset does not exist", "Preset Manager"
            )
            return
        preset[item] = val
        return

    # _____________ Import/Export ____________#

    def ExportJSON(self):
        """ """
        fileName = ui.chooseFile(
            load=False,
            start="Presets_.json",
            fileTypes=["json"],
            title="Save preset as:",
        )
        if fileName:
            with open(fileName, "w") as f:
                data = {}
                # getRaw() to strip dependable parts of presets dictionary to a serializable format
                # see https://docs.derivative.ca/TDStoreTools#Deeply_Dependable_Collections
                presetsDict = self.Presets.getRaw()
                data["presets"] = dict(presetsDict)
                json.dump(data, f, sort_keys=True, indent=4)
            self.ReportResult("Presets succesfully exported", "Preset Manager")
        else:
            self.ReportResult("No file was created", "Preset Manager")
        return

    def InjectPresets(self, presets):
        self.Presets.clear()
        self.Presets = presets
        return

    def ImportJSON(self):
        """
        This is the normal way of importing presets in this
        object. Files for this object do not contain bindings
        information.
        """
        fileName = ui.chooseFile(
            load=True, fileTypes=["json"], title="Load TDMorph preset"
        )
        if fileName:
            with open(fileName, "r") as f:
                data = json.load(f)
                self.Presets.clear()
                self.Presets = data["presets"]
            self.updatePresetsMenu()
            self.ReportResult("Presets succesfully imported", "Preset Manager")
        else:
            self.ReportResult("File was not imported", "Preset Manager")
        return

    # _____________ Setting/Morphing ____________#

    def GetEssentialStatesFrom(self, presetName):
        """
        This is used on presets interpolation. In that case,
        all we need to interpolate are already known parameters
        that do not use any filtering. That is why invokation to
        getEssentialStateFrom() is used.
        """
        preset = self.Presets.get(presetName, None)
        if preset is None:
            return None

        stored = preset["states"]
        states = {}

        for path in list(stored):
            target = op(path)

            if target is None:
                selection = ui.messageBox(
                    "Error",
                    "One or more nodes associated to this preset"
                    "have moved or are invalid. Should I remove invalid path from the database?",
                    buttons=["Yes", "Cancel"],
                )
                if selection == 0:
                    stored.pop(path)
                    continue
                return None

            data = stored[path]
            state = self.getEsssentialStateFrom(target, data)
            if state is not None:
                states[path] = state
            else:
                return None
        return states

    def GetEssentialStates(self):
        """
        Makes a dictionary with all the essential parameter
        states for morphing of all operators given by selected paths.
        """
        pathsData = op("Paths").Paths
        paths = list(pathsData.keys())
        states = {}

        for p in paths:
            target = op(p)

            if target is None:
                self.ReportResult(
                    "One or more of the nodes have moved or are invalid. "
                    "Make sure that you have correctly updated paths in the editor "
                    "before attempting morphing",
                    "Preset Manager",
                )
                return None

            data = pathsData[p]
            state = self.getEsssentialState(target, data)
            if state is not None:
                states[p] = state
            else:
                return None
        return states

    def GetStates(self, customWarning=None):
        """
        Makes a dictionary with all the current parameter
        states of all operators given by selected paths.
        """
        pathsData = op("Paths").Paths
        paths = list(pathsData.keys())
        states = {}
        for p in paths:
            target = op(p)

            if target is None:
                warning = (
                    "One or more referenced nodes have moved or are invalid. "
                    "Please update paths in the editor"
                )
                if customWarning:
                    warning = customWarning
                self.ReportResult(warning, "Preset Manager")
                return None

            data = pathsData[p]
            state = self.getState(target, data)

            if state is not None:
                states[p] = state
            else:
                return None

        return states

    def GetPresetsKeys(self):
        return list(self.Presets.keys())

    def GetNumPresets(self):
        return len(self.GetPresetsKeys())

    def GetMorphCurvesNames(self):
        return op("PresetMorpher/CurvesGenerator").par.Curves.menuNames

    def GetRandomDistributionNames(self):
        return op("RandomGenerator").RandomDistributions

    def GetElementsPaths(self):
        return op("Paths").GetPathsKeys()

    def ClearPresets(self, overwriteWarning=False):
        selection = True
        n = self.GetNumPresets()

        if n < 1:
            return

        if not overwriteWarning:
            text = "Are you sure you want to delete all presets?"
            selection = ui.messageBox("Warning", text, buttons=["Proceed", "Cancel"])
            selection = not bool(selection)

        if selection:
            self.Presets.clear()
            self.updatePresetsMenu()
        return

    def ReportResult(self, msg, title):
        debug("TDMorph")
        debug("\t{}".format(msg))
        op.TDResources.op("popDialog").Open(
            text=msg,
            title=title,
            buttons=["Ok"],
            escOnClickAway=True,
            escButton=1,
            enterButton=1,
            textEntry=False,
        )
        return

    def inject(self, preset, newKey, oldKey):
        """
        Inject a data block in the database, overwriting
        pre-existing one.
        """
        states = preset["states"]
        data = states.get(oldKey, None)
        if data:
            states[newKey] = data
            states.pop(oldKey)
        return

    def UpdatePath(self, oldPath, newPath):
        """
        Having to loop thorough all the presets to find
        the paths of allocated data is not very elegant.
        Try to think of an alternative.
        """
        if oldPath != newPath:
            for k in self.Presets:
                preset = self.Presets[k]
                self.inject(preset, newPath, oldPath)
        return

    def DeletePreset(self, name=None):
        if name is None:
            name = self.ownerComp.par.Presetname.eval()
        self.Presets.pop(name, None)
        self.updatePresetsMenu()
        return

    def StorePreset(self, name=None):
        """
        Create a preset in the databse, various checks
        take place to try and ensure that data does not
        get corrupted.
        """
        if name is None:
            name = self.ownerComp.par.Presetname.eval()
        states = self.GetStates()

        # Terminate if there's an error in state acquisition
        if states is None:
            return

        # Only store if something found
        if len(states) > 0:
            self.Presets[str(name)] = {
                "states": states,
                "time": self.MorphTime,
                "curve": self.MorphCurve,
                "distr": self.RandomDistribution,
            }
        else:
            # rosofo: Small modification to make the message less obtrusive
            debug("transit: No parameters found to store in preset")

        self.updatePresetsMenu()
        return

    def StorePresetWithData(self, name, data):
        """
        Stores a preset in the local storage of this component.
        It does so with given data, unlike the StorePreset method,
        which grabs current parameters state
        """
        self.Presets[str(name)] = data
        self.updatePresetsMenu()
        return

    def SetPreset(self, name=None):
        """
        Set the preset with the given name, without any
        interpolation.
        """
        if name is None:
            name = self.ownerComp.par.Presetname.eval()
        preset = self.Presets.get(name, None)

        if preset is None:
            self.ReportResult("Preset name not found", "Preset Manager")
            return

        states = preset["states"]
        for path in list(states):
            target = op(path)

            # Check node
            if target is None:
                selection = ui.messageBox(
                    "Error",
                    "Node {} has been removed or is invalid."
                    "Should I remove it from the database?".format(path),
                    buttons=["Yes", "Cancel"],
                )
                if selection == 0:
                    states.pop(path)
                    continue
                return

            # Check states
            params = states[path]
            for i, p in enumerate(params):
                param = p["paramName"]
                exists = hasattr(target.par, param)
                if exists:
                    target.par[param] = p["value"]
                else:
                    selection = ui.messageBox(
                        "Error",
                        "Parameter {} has been removed or is invalid."
                        "Should I remove it from the database?".format(param),
                        buttons=["Yes", "Cancel"],
                    )

                    if selection == 0:
                        params.pop(i)
                        continue

        return

    def MorphPreset(self, presetName, morphTime=None, morphCurve=None):
        """
        A wrapper of the PresetMorpher module. It morphs from
        current preset to presetName in morphTime seconds using
        the given morphCurve for interpolation.
        """
        op("PresetMorpher").MorphPreset(
            presetName, morphTime=morphTime, morphCurve=morphCurve
        )
        return

    def SetRandom(self, mode=None):
        """
        Generates random values for the targeted operators
        based on auto or single change.
        """
        if self.AutoMode:
            op("PresetMorpher").AutoRandomize(mode)
        else:
            op("PresetMorpher").SetRandom(mode)
        return

    def MorphRandom(self, mode=None):
        """
        Set random values with morphing functionality based on
        auto or single change
        """
        if self.AutoMode:
            op("PresetMorpher").AutoRandomMorph(mode)
        else:
            op("PresetMorpher").MorphRandom(mode)
        return

    def StopMorphing(self):
        op("PresetMorpher").StopMorphing()
        return

    def PlayMorphing(self, play=True):
        op("PresetMorpher").PlayMorphing(play)
        return

    def PresetsSequence(self, sortKeys=False, keysSequence=None):
        op("PresetMorpher").PresetsSequence(
            sortKeys=sortKeys, keysSequence=keysSequence
        )
        return

    def SetBlendingPresets(self, presetName, targetName):
        op("PresetMorpher").SetBlendingPresets(presetName, targetName)
        return

    def RandomizeGivenParameters(self, operatorIndex, names, mode=None):
        op("PresetMorpher").RandomizeGivenParameters(operatorIndex, names, mode)
        return

    def MorphGivenParameters(self, operatorIndex, names, mode=None):
        op("PresetMorpher").MorphGivenParameters(operatorIndex, names, mode)
        return

    # _________ Overwrites _______ #

    def OverwritePresetsValue(self, item, val):
        """
        Used to overwrite a specific item in the parameter list.
        Will overwrite the value for all presets. This is invoked
        in an element MorphSettings to execute local random/morphs
        """
        for k in self.Presets:
            self.Presets[k][item] = val
        return

    def OverwriteCurrentPreset(self):
        self.StorePreset(name=self.ownerComp.par.Target.eval())
        return
