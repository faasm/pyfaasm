import numpy as np
from numpy import int32

from pyfaasm.config import MATRIX_CONF_STATE_KEY, SUBMATRICES_KEY_A, SUBMATRICES_KEY_B, \
    RESULT_MATRIX_KEY, get_submatrix_byte_offset, NP_ELEMENT_SIZE, generate_matrix_conf
from pyfaasm.core import setState, getStateOffset, getState, chainThisWithInput, awaitCall, setStateOffset, \
    registerFunction, pushStatePartial
from pyfaasm.matrix_data import do_subdivide_matrix, do_reconstruct_matrix


def write_matrix_params_to_state(matrix_size, n_splits):
    params = np.array((matrix_size, n_splits), dtype=int32)
    setState(MATRIX_CONF_STATE_KEY, params.tobytes())


def load_matrix_conf_from_state():
    # Params are ints so need to work out what size they are
    dummy = np.array((1, 2), dtype=int32)
    param_len = len(dummy.tobytes())
    param_bytes = getState(MATRIX_CONF_STATE_KEY, param_len)
    params = np.frombuffer(param_bytes, dtype=int32)

    matrix_size = params[0]
    n_splits = params[1]

    conf = generate_matrix_conf(matrix_size, n_splits)

    print("---- Matrix config ----")
    print("np_element_size {}".format(NP_ELEMENT_SIZE))
    print("matrix_size {}".format(conf.matrix_size))
    print("n_splits {}".format(conf.n_splits))
    print("submatrices_per_row {}".format(conf.submatrices_per_row))
    print("submatrix_size {}".format(conf.submatrix_size))
    print("bytes_per_submatrix {}".format(conf.bytes_per_submatrix))
    print("bytes_per_matrix {}".format(conf.bytes_per_matrix))

    return conf


# Create a random matrix split up in state
def subdivide_random_matrix_into_state(conf, key):
    # Step through rows and columns of original matrix, generating random submatrices
    all_bytes = b''
    for row_idx in range(0, conf.submatrices_per_row):
        for col_idx in range(0, conf.submatrices_per_row):
            sub_mat = np.random.rand(conf.submatrix_size, conf.submatrix_size)
            all_bytes += sub_mat.tobytes()

    setState(key, all_bytes)


# Split up the original matrix into square submatrices and write to state
# Write each submatrix as a region of contiguous bytes
# All submatrices appended into one byte stream
def subdivide_matrix_into_state(conf, mat, key):
    all_bytes = do_subdivide_matrix(conf, mat)
    setState(key, all_bytes)


# Reads a given submatrix from state
def read_submatrix_from_state(conf, key, row_idx, col_idx):
    offset = get_submatrix_byte_offset(conf, row_idx, col_idx)
    sub_mat_bytes = getStateOffset(key, conf.bytes_per_matrix, offset, conf.bytes_per_submatrix)
    return np.frombuffer(sub_mat_bytes).reshape(conf.submatrix_size, conf.submatrix_size)


# Rebuilds a matrix from its submatrices in state
def reconstruct_matrix_from_submatrices(conf, key):
    all_bytes = getState(key, conf.bytes_per_matrix)
    return do_reconstruct_matrix(conf, all_bytes)


def do_multiplication(conf, quad_row_idx, quad_col_idx):
    row_idx = quad_row_idx * 2
    col_idx = quad_col_idx * 2

    # Read in the four quadrants of each input matrix
    mat_aa = read_submatrix_from_state(conf, SUBMATRICES_KEY_A, row_idx, col_idx)
    mat_ab = read_submatrix_from_state(conf, SUBMATRICES_KEY_A, row_idx, col_idx + 1)
    mat_ac = read_submatrix_from_state(conf, SUBMATRICES_KEY_A, row_idx + 1, col_idx)
    mat_ad = read_submatrix_from_state(conf, SUBMATRICES_KEY_A, row_idx + 1, col_idx + 1)

    mat_ba = read_submatrix_from_state(conf, SUBMATRICES_KEY_B, row_idx, col_idx)
    mat_bb = read_submatrix_from_state(conf, SUBMATRICES_KEY_B, row_idx, col_idx + 1)
    mat_bc = read_submatrix_from_state(conf, SUBMATRICES_KEY_B, row_idx + 1, col_idx)
    mat_bd = read_submatrix_from_state(conf, SUBMATRICES_KEY_B, row_idx + 1, col_idx + 1)

    # Do the actual multiplication
    r_a = np.dot(mat_aa, mat_ba) + np.dot(mat_ab, mat_bc)
    r_b = np.dot(mat_aa, mat_bb) + np.dot(mat_ab, mat_bd)
    r_c = np.dot(mat_ac, mat_ba) + np.dot(mat_ad, mat_bc)
    r_d = np.dot(mat_ac, mat_bb) + np.dot(mat_ad, mat_bd)

    # Construct the result
    result = np.concatenate((
        np.concatenate((r_a, r_b), axis=1),
        np.concatenate((r_c, r_d), axis=1)
    ), axis=0)

    # Write to state
    result_offset = get_submatrix_byte_offset(conf, row_idx, col_idx)
    setStateOffset(RESULT_MATRIX_KEY, conf.bytes_per_matrix, result_offset, result.tobytes())
    pushStatePartial(RESULT_MATRIX_KEY)


def distributed_divide_and_conquer(input_bytes):
    conf = load_matrix_conf_from_state()

    # This is designed to be invoked by Faasm
    input_args = np.frombuffer(input_bytes, dtype=int32)

    quadrant_row_idx = input_args[0]
    quadrant_col_idx = input_args[1]

    print("Doing multiplication QUAD ROW {} QUAD COL {}".format(quadrant_row_idx, quadrant_col_idx))
    do_multiplication(conf, quadrant_row_idx, quadrant_col_idx)


def divide_and_conquer():
    conf = load_matrix_conf_from_state()
    print("Running divide and conquer for {}x{} matrix with {} splits".format(
        conf.matrix_size,
        conf.matrix_size,
        conf.n_splits
    ))

    # To keep things working in native python
    registerFunction(1, distributed_divide_and_conquer)

    # Kick off all the multiplication jobs
    # Note that the arguments to
    call_ids = []
    for quadrant_row_idx in range(0, conf.quadrants_per_row):
        for quadrant_col_idx in range(0, conf.quadrants_per_row):
            inputs = np.array([quadrant_row_idx, quadrant_col_idx])
            call_id = chainThisWithInput(1, inputs.tobytes())
            call_ids.append(call_id)

    # Await completion
    for call_id in call_ids:
        awaitCall(call_id)
