import numpy as np
from numpy import int32

from pyfaasm.core import setState, getStateOffset, getState, chainThisWithInput, awaitCall, setStateOffset, \
    registerFunction, pushStatePartial

# NOTE: we are assuming numpy floats are 8 bytes here
NP_ELEMENT_SIZE = 8

SUBMATRICES_KEY_A = "submatrices_a"
SUBMATRICES_KEY_B = "submatrices_b"
RESULT_MATRIX_KEY = "result_matrix"
MATRIX_CONF_STATE_KEY = "matrix_state"


class MatrixConf:
    initialised = False
    matrix_size = 0
    n_splits = 0
    bytes_per_matrix = 0
    submatrices_per_row = 0
    quadrants_per_row = 0
    submatrix_size = 0
    bytes_per_submatrix = 0


def write_matrix_params_to_state(matrix_size, n_splits):
    params = np.array((matrix_size, n_splits), dtype=int32)
    setState(MATRIX_CONF_STATE_KEY, params.tobytes())


def load_matrix_conf_from_state():
    if MatrixConf.initialised:
        return

    MatrixConf.initialised = True

    # Params are ints so need to work out what size they are
    dummy = np.array((1, 2), dtype=int32)
    param_len = len(dummy.tobytes())
    param_bytes = getState(MATRIX_CONF_STATE_KEY, param_len)
    params = np.frombuffer(param_bytes, dtype=int32)

    matrix_size = params[0]
    n_splits = params[1]

    # Remember we're dealing with square matrices and splitting the matrix into
    # four pieces each time we do the divide in the divide and conquer.
    # The number of splits is how many times we're dividing the origin matrices.

    MatrixConf.matrix_size = matrix_size
    MatrixConf.n_splits = n_splits
    MatrixConf.bytes_per_matrix = (matrix_size * matrix_size) * NP_ELEMENT_SIZE
    MatrixConf.submatrices_per_row = 2 ** n_splits
    MatrixConf.quadrants_per_row = 2 ** (n_splits - 1)
    MatrixConf.submatrix_size = matrix_size // MatrixConf.submatrices_per_row
    MatrixConf.bytes_per_submatrix = (MatrixConf.submatrix_size * MatrixConf.submatrix_size) * NP_ELEMENT_SIZE

    print("---- Matrix divide and conquer ----")
    print("np_element_size {}".format(NP_ELEMENT_SIZE))
    print("matrix_size {}".format(MatrixConf.matrix_size))
    print("n_splits {}".format(MatrixConf.n_splits))
    print("submatrices_per_row {}".format(MatrixConf.submatrices_per_row))
    print("submatrix_size {}".format(MatrixConf.submatrix_size))
    print("bytes_per_submatrix {}".format(MatrixConf.bytes_per_submatrix))
    print("bytes_per_matrix {}".format(MatrixConf.bytes_per_matrix))


# Returns the offset of a given submatrix in the overall byte array
def _get_submatrix_byte_offset(row_idx, col_idx):
    return (row_idx * MatrixConf.bytes_per_submatrix * MatrixConf.submatrices_per_row) + \
           (col_idx * MatrixConf.bytes_per_submatrix)


# Create a random matrix split up in state
def subdivide_random_matrix_into_state(key):
    # Step through rows and columns of original matrix, generating random submatrices
    all_bytes = b''
    for row_idx in range(0, MatrixConf.submatrices_per_row):
        for col_idx in range(0, MatrixConf.submatrices_per_row):
            sub_mat = np.random.rand(MatrixConf.submatrix_size, MatrixConf.submatrix_size)
            all_bytes += sub_mat.tobytes()

    setState(key, all_bytes)


# Split up the original matrix into square submatrices and write to state
# Write each submatrix as a region of contiguous bytes
# All submatrices appended into one byte stream
def subdivide_matrix_into_state(mat, key):
    _do_subdivide_matrix(mat, state_key=key)


def subdivide_matrix_into_file(mat, file_path):
    _do_subdivide_matrix(mat, file_path=file_path)


def _do_subdivide_matrix(mat, state_key=None, file_path=None):
    # Step through rows and columns of original matrix, appending submatrix bytes
    # to the overall byte stream
    all_bytes = b''
    for row_idx in range(0, MatrixConf.submatrices_per_row):
        for col_idx in range(0, MatrixConf.submatrices_per_row):
            # Work out the position of the top left and bottom right corner of the submatrix
            row_start = row_idx * MatrixConf.submatrix_size
            col_start = col_idx * MatrixConf.submatrix_size

            row_end = row_start + MatrixConf.submatrix_size
            col_end = col_start + MatrixConf.submatrix_size

            # Extract the submatrix and write to bytes
            sub_mat = mat[row_start:row_end, col_start:col_end]
            all_bytes += sub_mat.tobytes()

    # Write these bytes to state
    if state_key:
        setState(state_key, all_bytes)
    elif file_path:
        with open(file_path, "wb") as fh:
            fh.write(all_bytes)
    else:
        print("Must specify state or file as destination")


# Reads a given submatrix from state
def read_submatrix_from_state(key, row_idx, col_idx):
    offset = _get_submatrix_byte_offset(row_idx, col_idx)
    sub_mat_bytes = getStateOffset(key, MatrixConf.bytes_per_matrix, offset, MatrixConf.bytes_per_submatrix)
    return np.frombuffer(sub_mat_bytes).reshape(MatrixConf.submatrix_size, MatrixConf.submatrix_size)


def reconstruct_matrix_from_file(file_path):
    with open(file_path, "rb") as fh:
        all_bytes = fh.read()

    return _do_reconstruct_matrix(all_bytes)


# Rebuilds a matrix from its submatrices in state
def reconstruct_matrix_from_submatrices(key):
    all_bytes = getState(key, MatrixConf.bytes_per_matrix)
    return _do_reconstruct_matrix(all_bytes)


def _do_reconstruct_matrix(all_bytes):
    result = None

    # Need to read in row by row concatenate the rows
    for row_idx in range(0, MatrixConf.submatrices_per_row):
        submatrices = []
        for col_idx in range(0, MatrixConf.submatrices_per_row):
            byte_idx = _get_submatrix_byte_offset(row_idx, col_idx)
            this_submat = np.frombuffer(all_bytes[byte_idx: byte_idx + MatrixConf.bytes_per_submatrix])
            this_submat = this_submat.reshape(MatrixConf.submatrix_size, MatrixConf.submatrix_size)
            submatrices.append(this_submat)

        this_row = np.concatenate(submatrices, axis=1)

        if row_idx == 0:
            # Initialise the result
            result = this_row
        else:
            # Add the row to the existing result
            result = np.concatenate((result, this_row), axis=0)

    return result


def do_multiplication(quad_row_idx, quad_col_idx):
    row_idx = quad_row_idx * 2
    col_idx = quad_col_idx * 2

    # Read in the four quadrants of each input matrix
    mat_aa = read_submatrix_from_state(SUBMATRICES_KEY_A, row_idx, col_idx)
    mat_ab = read_submatrix_from_state(SUBMATRICES_KEY_A, row_idx, col_idx + 1)
    mat_ac = read_submatrix_from_state(SUBMATRICES_KEY_A, row_idx + 1, col_idx)
    mat_ad = read_submatrix_from_state(SUBMATRICES_KEY_A, row_idx + 1, col_idx + 1)

    mat_ba = read_submatrix_from_state(SUBMATRICES_KEY_B, row_idx, col_idx)
    mat_bb = read_submatrix_from_state(SUBMATRICES_KEY_B, row_idx, col_idx + 1)
    mat_bc = read_submatrix_from_state(SUBMATRICES_KEY_B, row_idx + 1, col_idx)
    mat_bd = read_submatrix_from_state(SUBMATRICES_KEY_B, row_idx + 1, col_idx + 1)

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
    result_offset = _get_submatrix_byte_offset(row_idx, col_idx)
    setStateOffset(RESULT_MATRIX_KEY, MatrixConf.bytes_per_matrix, result_offset, result.tobytes())
    pushStatePartial(RESULT_MATRIX_KEY)


def distributed_divide_and_conquer(input_bytes):
    load_matrix_conf_from_state()

    # This is designed to be invoked by Faasm
    input_args = np.frombuffer(input_bytes, dtype=int32)

    quadrant_row_idx = input_args[0]
    quadrant_col_idx = input_args[1]

    print("Doing multiplication QUAD ROW {} QUAD COL {}".format(quadrant_row_idx, quadrant_col_idx))
    do_multiplication(quadrant_row_idx, quadrant_col_idx)


def divide_and_conquer():
    load_matrix_conf_from_state()

    # To keep things working in native python
    registerFunction(1, distributed_divide_and_conquer)

    # Kick off all the multiplication jobs
    # Note that the arguments to
    call_ids = []
    for quadrant_row_idx in range(0, MatrixConf.quadrants_per_row):
        for quadrant_col_idx in range(0, MatrixConf.quadrants_per_row):
            inputs = np.array([quadrant_row_idx, quadrant_col_idx])
            call_id = chainThisWithInput(1, inputs.tobytes())
            call_ids.append(call_id)

    # Await completion
    for call_id in call_ids:
        awaitCall(call_id)
