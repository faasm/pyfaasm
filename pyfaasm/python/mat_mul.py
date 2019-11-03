from pyfaasm.core import getFunctionIdx, getInput
from pyfaasm.matrix import divide_and_conquer, distributed_divide_and_conquer, \
    load_matrix_conf_from_state


def main_func():
    idx = getFunctionIdx()

    if idx == 0:
        load_matrix_conf_from_state()
        divide_and_conquer()
    else:
        input_bytes = getInput()
        distributed_divide_and_conquer(input_bytes)


if __name__ == "__main__":
    main_func()
