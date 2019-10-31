import numpy as np

from pyfaasm.core import setState, getStateOffset, getState, getFunctionIdx, chainThisWithInput, awaitCall, getInput, \
    setStateOffset, registerFunction

# NOTE: we are assuming numpy floats are 8 bytes here
NP_ELEMENT_SIZE = 8

# Remember we're dealing with square matrices and splitting the matrix into
# four pieces each time we do the divide in the divide and conquer.
# The number of splits is how many times we're dividing the origin matrices.
MATRIX_SIZE = 1000
TOTAL_BYTES_PER_MATRIX = (MATRIX_SIZE * MATRIX_SIZE) * NP_ELEMENT_SIZE

N_SPLITS = 3
SUBMATRICES_PER_ROW = 2 ** N_SPLITS
QUADRANTS_PER_ROW = 2 ** (N_SPLITS - 1)
SUBMATRIX_SIZE = MATRIX_SIZE // SUBMATRICES_PER_ROW
BYTES_PER_SUBMATRIX = (SUBMATRIX_SIZE * SUBMATRIX_SIZE) * NP_ELEMENT_SIZE

SUBMATRICES_KEY_A = "submatrices_a"
SUBMATRICES_KEY_B = "submatrices_b"
RESULT_MATRIX_KEY = "result_matrix"


# Returns the offset of a given submatrix in the overall byte array
def _get_submatrix_byte_offset(row_idx, col_idx):
    return (row_idx * BYTES_PER_SUBMATRIX * SUBMATRICES_PER_ROW) + (col_idx * BYTES_PER_SUBMATRIX)


# Split up the original matrix into square submatrices and write to state
# Write each submatrix as a region of contiguous bytes
# All submatrices appended into one byte stream
def subdivide_matrix_into_state(mat, key):
    # Step through rows and columns of original matrix, appending submatrix bytes
    # to the overall byte stream
    all_bytes = b''
    for row_idx in range(0, SUBMATRICES_PER_ROW):
        for col_idx in range(0, SUBMATRICES_PER_ROW):
            # Work out the position of the top left and bottom right corner of the submatrix
            row_start = row_idx * SUBMATRIX_SIZE
            col_start = col_idx * SUBMATRIX_SIZE

            row_end = row_start + SUBMATRIX_SIZE
            col_end = col_start + SUBMATRIX_SIZE

            # Extract the submatrix and write to bytes
            sub_mat = mat[row_start:row_end, col_start:col_end]
            all_bytes += sub_mat.tobytes()

    # Write these bytes to state
    setState(key, all_bytes)


# Reads a given submatrix from state
def read_submatrix_from_state(key, row_idx, col_idx):
    offset = _get_submatrix_byte_offset(row_idx, col_idx)
    sub_mat_bytes = getStateOffset(key, TOTAL_BYTES_PER_MATRIX, offset, BYTES_PER_SUBMATRIX)
    return np.frombuffer(sub_mat_bytes).reshape(SUBMATRIX_SIZE, SUBMATRIX_SIZE)


# Rebuilds a matrix from its submatrices in state
def reconstruct_matrix_from_submatrices(key):
    all_bytes = getState(key, TOTAL_BYTES_PER_MATRIX)

    result = None

    # Need to read in row by row concatenate the rows
    for row_idx in range(0, SUBMATRICES_PER_ROW):
        submatrices = []
        for col_idx in range(0, SUBMATRICES_PER_ROW):
            byte_idx = _get_submatrix_byte_offset(row_idx, col_idx)
            this_submat = np.frombuffer(all_bytes[byte_idx: byte_idx + BYTES_PER_SUBMATRIX])
            this_submat = this_submat.reshape(SUBMATRIX_SIZE, SUBMATRIX_SIZE)
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
    setStateOffset(RESULT_MATRIX_KEY, TOTAL_BYTES_PER_MATRIX, result_offset, result.tobytes())


def distributed_divide_and_conquer(input_bytes):
    # This is designed to be invoked by Faasm
    input_args = np.frombuffer(input_bytes, dtype=int)

    quadrant_row_idx = input_args[0]
    quadrant_col_idx = input_args[1]

    print("Doing multiplication QUAD ROW {} QUAD COL {}".format(quadrant_row_idx, quadrant_col_idx))
    do_multiplication(quadrant_row_idx, quadrant_col_idx)


def divide_and_conquer():
    print("---- Matrix divide and conquer ----")
    print("NP_ELEMENT_SIZE {}".format(NP_ELEMENT_SIZE))
    print("MATRIX_SIZE {}".format(MATRIX_SIZE))
    print("N_SPLITS {}".format(N_SPLITS))
    print("SUBMATRICES_PER_ROW {}".format(SUBMATRICES_PER_ROW))
    print("SUBMATRIX_SIZE {}".format(SUBMATRIX_SIZE))
    print("BYTES_PER_SUBMATRIX {}".format(BYTES_PER_SUBMATRIX))
    print("TOTAL_BYTES_PER_MATRIX {}".format(TOTAL_BYTES_PER_MATRIX))

    # To keep things working in native python
    registerFunction(1, distributed_divide_and_conquer)

    # Zero the result
    zero_result = np.zeros((MATRIX_SIZE, MATRIX_SIZE))
    setState(RESULT_MATRIX_KEY, zero_result.tobytes())

    # Kick off all the multiplication jobs
    # Note that the arguments to
    call_ids = []
    for quadrant_row_idx in range(0, QUADRANTS_PER_ROW):
        for quadrant_col_idx in range(0, QUADRANTS_PER_ROW):
            inputs = np.array([quadrant_row_idx, quadrant_col_idx])
            call_id = chainThisWithInput(1, inputs.tobytes())
            call_ids.append(call_id)

    # Await completion
    for call_id in call_ids:
        awaitCall(call_id)
