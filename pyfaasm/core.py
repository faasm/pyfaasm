import pyfaasm.cfaasm as cf


def checkPythonBindings():
    # This should return a valid string
    message = cf.hello_faasm()
    print(message)

    # Check the hard-coded dummy input
    actual_input = cf.check_input()
    expected_input = b'01234'
    if type(actual_input == bytes) and actual_input == expected_input:
        print("Got expected input {}".format(actual_input))
    else:
        print("Did not get expected input (expected {}, actual {})".format(expected_input, actual_input))
