from pyfaasm.core import getInput, setOutput


def main_func():
    i = getInput()

    if i:
        print("Got input {}".format(i))
        setOutput(bytes(i))


if __name__ == "__main__":
    main_func()
