from pyfaasm.core import checkPythonBindings
from pyfaasm.core import getState, getStateOffset, setState, setStateOffset, pushState, pullState

# Initial check
checkPythonBindings()

# Write and push state
key = "pyStateTest"
valueLen = 10
fullValue = b'0123456789'
setState(key, fullValue)
pushState(key)

# Read state back in
pullState(key, valueLen)
actual = getState(key, valueLen)
print("In = {}  out = {}".format(fullValue, actual))

# Update a segment
segment = b'999'
offset = 2
segmentLen = 3
modifiedValue = b'0199956789'
setStateOffset(key, valueLen, offset, segment)
pushState(key)

pullState(key, valueLen)
actual = getState(key, valueLen)
actualSegment = getStateOffset(key, valueLen, offset, segmentLen)
print("Expected = {}  actual = {}".format(modifiedValue, actual))
print("Expected = {}  actual = {}".format(segment, actualSegment))
