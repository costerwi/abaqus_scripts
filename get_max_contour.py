# Abaqus Python Script
# Loop through results to find max controur value for each increment.
# Use File->Run Script... to execute

# Get active viewport and odb
vp = session.viewports[session.currentViewportName]
od = vp.odbDisplay

# Collect the data
xy = []
for step_num, step in enumerate(od.fieldSteps):
    for frame_num, frame in enumerate(step[8]):
        od.setFrame(step=step_num, frame=frame_num)
        xy.append([step[2] + frame, od.contourOptions.autoMaxValue])

# Find a unique name for the XY data
exists = n = 1
while exists:
    name = 'Max-{}'.format(n)
    exists = name in session.xyDataObjects
    n += 1

# Store data in an XYData object
xydata = session.XYData(name=name,
    data=xy,
    sourceDescription='from script',
    contentDescription='Max {}'.format(od.primaryVariableLabel),
    )

print("Created xy data {}".format(name))
