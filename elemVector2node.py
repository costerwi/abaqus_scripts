"""elemVector2node.py

Test script to convert whole-element vector fieldoutput into nodal averaged 
field output for postprocessing with streams in Abaqus/CAE

Run from File->Run Script...

Carl Osterwisch <osterwisch@caelynx.com>
August 2016
"""
               
from __future__ import print_function

import numpy as np
import abaqus
import abaqusConstants

def getCurrentFrame(odbDisplay=None):
    "Return the current odb result frame"
    import abaqus

    odb = step = frame = None
    if not odbDisplay:
        odbDisplay = abaqus.session.viewports[
                abaqus.session.currentViewportName].odbDisplay

    if hasattr(odbDisplay, "fieldFrame"):
        odb = abaqus.session.odbs[odbDisplay.name]
        frameId = odbDisplay.fieldFrame
        frame = None
        if isinstance(frameId[0], int):
            step = odb.steps.values()[frameId[0]]
            if len(step.frames):
                frame=step.frames[frameId[1]]
        else:
            step = abaqus.session.ScratchOdb(odb).steps[frameId[0]]
            if len(step.frames):
                # Abaqus 6.10 returns 4 values.  Abaqus 6.9 returned 3.
                # The last value is the frame number in both cases.
                frame=step.frames[frameId[-1]]
    return odb, step, frame


odb, step, frame = getCurrentFrame()

scratchOdb = abaqus.session.ScratchOdb(odb)
scratchStepName = step.name + ' scratch'
if scratchOdb.steps.has_key(scratchStepName):
    scratchStep = scratchOdb.steps[scratchStepName]
    print('Appending to scratch step {}'.format(scratchStep.name))
else:
    scratchStep = scratchOdb.Step(
            name=scratchStepName, 
            description=step.description,
            domain=abaqusConstants.TIME, 
            timePeriod=1.)
    print('Created new scratch step {}'.format(scratchStep.name))

scratchFrame = scratchStep.Frame(
        frameId = len(scratchStep.frames),
        frameValue = 1., 
        description = frame.description)
print('Created scratch frame {} {}'.format(scratchFrame.frameId, scratchFrame.description))

for fo in frame.fieldOutputs.values():
    if not abaqusConstants.VECTOR == fo.type:
        continue # skip non vector outputs
    print('{} {} elemental results'.format(fo.name, len(fo.values)), end='')

    # Group results by instance and node for averaging
    instData = {}
    for v in fo.values:
        elem = v.instance.getElementFromLabel(v.elementLabel)
        for i, n in zip(elem.instanceNames, elem.connectivity):
            instData.setdefault(i, {}).setdefault(n, []).append(v.data)
    
    field = frame.FieldOutput(
            name=fo.name + '_', 
            description=fo.description,
            type=abaqusConstants.VECTOR,
            validInvariants=(abaqusConstants.MAGNITUDE,))

    # Add data for each instance
    for instName, nodalData in instData.items():
        sortedIDs = nodalData.keys()
        sortedIDs.sort()
        print(' -> {} {} nodal averaged results'.format(instName, len(sortedIDs)))

        field.addData(
                position=abaqusConstants.NODAL,
                instance=odb.rootAssembly.instances[instName], 
                labels=sortedIDs,
                data=[np.average(nodalData[id], axis=0) for id in sortedIDs])

    # Copy fieldoutput into scratch frame for viewing
    scratchFrame.FieldOutput(field, name=fo.name)

print('Done.')
 
