import os

import pyfaasm.cfaasm as cf

PYTHON_LOCAL_CHAINING = bool(os.environ.get("PYTHON_LOCAL_CHAINING"))
PYTHON_LOCAL_INPUT_OUTPUT = bool(os.environ.get("PYTHON_LOCAL_INPUT_OUTPUT"))

REGISTERED_FUNCTIONS = {}

input_data = None
output_data = None
func_idx = 0


def setLocalChaining(value):
    global PYTHON_LOCAL_CHAINING
    PYTHON_LOCAL_CHAINING = value


def setLocalInputOutput(value):
    global PYTHON_LOCAL_INPUT_OUTPUT
    PYTHON_LOCAL_INPUT_OUTPUT = value


def registerFunction(idx, func):
    global REGISTERED_FUNCTIONS
    REGISTERED_FUNCTIONS[idx] = func


def clearRegisteredFunctions():
    global REGISTERED_FUNCTIONS
    REGISTERED_FUNCTIONS = {}


def checkPythonBindings():
    # This should return a valid string
    message = cf.hello_faasm()
    print(message)

    # Check the hard-coded dummy input
    actual_input = cf.check_input()
    expected_input = b'01234'
    if type(actual_input == bytes) and actual_input == expected_input:
        print("Got expected input {} (expected {})".format(actual_input, expected_input))
    else:
        print("Did not get expected input (expected {}, actual {})".format(expected_input, actual_input))

    # Check function index
    print("Function idx = {}".format(getFunctionIdx()))


def setInput(d):
    if PYTHON_LOCAL_INPUT_OUTPUT:
        global input_data
        input_data = d
    else:
        raise RuntimeError("Should not be setting input in non-local input/output")


def getInput():
    if PYTHON_LOCAL_INPUT_OUTPUT:
        global input_data
        return input_data
    else:
        return cf.faasm_get_input()


def setOutput(output):
    if PYTHON_LOCAL_INPUT_OUTPUT:
        global output_data
        output_data = output
    else:
        cf.faasm_set_output(output)


def getOutput():
    if PYTHON_LOCAL_INPUT_OUTPUT:
        global output_data
        return output_data
    else:
        raise RuntimeError("Should not be getting output in non-local input/ output")


def getState(key, len):
    return cf.faasm_get_state(key, len)


def getStateOffset(key, total_len, offset, offset_len):
    return cf.faasm_get_state_offset(key, total_len, offset, offset_len)


def setState(key, value):
    cf.faasm_set_state(key, value)


def setStateOffset(key, total_len, offset, value):
    cf.faasm_set_state_offset(key, total_len, offset, value)


def pushState(key):
    cf.faasm_push_state(key)


def pushStatePartial(key):
    cf.faasm_push_state_partial(key)


def pullState(key, state_len):
    cf.faasm_pull_state(key, state_len)


def setFunctionIdx(idx):
    if PYTHON_LOCAL_INPUT_OUTPUT:
        global func_idx
        func_idx = idx
    else:
        raise RuntimeError("Should not be setting index in non-local input/output")


def getFunctionIdx():
    if PYTHON_LOCAL_INPUT_OUTPUT:
        global func_idx
        return func_idx
    else:
        return cf.faasm_get_idx()


def chainThisWithInput(function_idx, input_data):
    if PYTHON_LOCAL_CHAINING:
        # Run function directly
        REGISTERED_FUNCTIONS[function_idx](input_data)
        return 0
    else:
        # Call native
        return cf.faasm_chain_this(function_idx, input_data)


def awaitCall(call_id):
    if PYTHON_LOCAL_CHAINING:
        # Calls are run immediately
        return 0
    else:
        # Call native
        return cf.faasm_await_call(call_id)


def getCallStatus(call_id):
    if PYTHON_LOCAL_CHAINING:
        # Calls are run immediately
        return "SUCCESS"
    else:
        return cf.get_call_status(call_id)
