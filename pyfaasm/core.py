import pyfaasm.cfaasm as cf


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


def getInput():
    return cf.faasm_get_input()


def setOutput(output):
    cf.faasm_set_output(output)


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


def pullState(key, state_len):
    cf.faasm_pull_state(key, state_len)


def getFunctionIdx():
    pass


def chainThisWithInput(function_idx, input_data):
    pass


def awaitCall(call_id):
    pass
