from _native import hello_faasm, check_input


def checkPythonBindings():
    # This should return a valid string
    message = hello_faasm()
    print(message)

    # Check the hard-coded dummy input
    actual_input = check_input()
    expected_input = b'01234'
    if type(actual_input == bytes) and actual_input == expected_input:
        print("Got expected input {}".format(actual_input))
    else:
        print("Did not get expected input (expected {}, actual {})".format(expected_input, actual_input))

