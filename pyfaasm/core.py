from _native import hello_faasm


def checkPythonBindings():
    message = hello_faasm()
    print(message)
