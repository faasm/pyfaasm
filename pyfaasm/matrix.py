import numpy as np

from pyfaasm.core import setState, getStateOffset, getState, getFunctionIdx, chainThisWithInput, awaitThis, getInput

# Work out the item size in a matrix by creating a dummy matrix
NP_ELEMENT_SIZE = np.array([1.1, 1.1], [1.1, 1.1]).itemsize

# Remember we're dealing with square matrices and splitting the matrix into
# four pieces each time we do the divide in the divide and conquer.
# The number of splits is how many times we're dividing the origin matrices.
MATRIX_SIZE = 12000
N_SPLITS = 3
SUBMATRICES_PER_ROW = 2 ** N_SPLITS
SUBMATRIX_SIZE = MATRIX_SIZE // SUBMATRICES_PER_ROW
BYTES_PER_SUBMATRIX = SUBMATRIX_SIZE * SUBMATRIX_SIZE * NP_ELEMENT_SIZE
BYTES_PER_ROW = BYTES_PER_SUBMATRIX * SUBMATRICES_PER_ROW
TOTAL_BYTES_PER_MATRIX = BYTES_PER_SUBMATRIX * SUBMATRICES_PER_ROW * SUBMATRICES_PER_ROW

SUBMATRICES_KEY_A = "submatrices_a"
SUBMATRICES_KEY_B = "submatrices_b"
RESULT_MATRIX_KEY = "result_matrix"


# Returns the offset of a given submatrix in the overall byte array
def _get_submatrix_byte_offset(row_idx, col_idx):
    return (row_idx * BYTES_PER_ROW) + (col_idx * BYTES_PER_SUBMATRIX)


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
    return np.frombuffer(sub_mat_bytes)


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
            submatrices.append(this_submat)

        this_row = np.concatenate(submatrices, axis=1)

        if row_idx == 0:
            # Initialise the result
            result = this_row
        else:
            # Add the row to the existing result
            result = np.concatenate((result, this_row), axis=0)

    return result


def do_multiplication(split_number, row_idx, col_idx):
    if split_number < N_SPLITS:
        # Do a further split and pass on. In the next split we're doubling the
        # number of submatrices in each row and column, so we double the row
        # and column indices
        split_number += 1
        row_idx *= 2
        col_idx *= 2

        # Do multiplication on the four submatrices
        call_a = do_multiplication(split_number, row_idx, col_idx)
        call_b = do_multiplication(split_number, row_idx, col_idx + 1)
        call_c = do_multiplication(split_number, row_idx + 1, col_idx)
        call_d = do_multiplication(split_number, row_idx + 1, col_idx + 1)

        awaitCall(call_a)
        awaitCall(call_b)
        awaitCall(call_c)
        awaitCall(call_d)
    else:
        # We're at the target number of splits, so do the multiplication
        # Read in the four quadrants of each input matrix
        mat_aa = read_submatrix_from_state(SUBMATRICES_KEY_A, row_idx, col_idx)
        mat_ab = read_submatrix_from_state(SUBMATRICES_KEY_A, row_idx, col_idx + 1)
        mat_ac = read_submatrix_from_state(SUBMATRICES_KEY_A, row_idx + 1, col_idx)
        mat_ad = read_submatrix_from_state(SUBMATRICES_KEY_A, row_idx + 1, col_idx + 1)

        mat_ba = read_submatrix_from_state(SUBMATRICES_KEY_B, row_idx, col_idx)
        mat_bb = read_submatrix_from_state(SUBMATRICES_KEY_B, row_idx, col_idx + 1)
        mat_bc = read_submatrix_from_state(SUBMATRICES_KEY_B, row_idx + 1, col_idx)
        mat_bd = read_submatrix_from_state(SUBMATRICES_KEY_B, row_idx + 1, col_idx + 1)

        r_a = np.dot(mat_aa, mat_ba) + np.dot(mat_ab, mat_bc)
        r_b = np.dot(mat_aa, mat_bb) + np.dot(mat_ab, mat_bd)
        r_c = np.dot(mat_ac, mat_ba) + np.dot(mat_ad, mat_bc)
        r_d = np.dot(mat_ac, mat_bb) + np.dot(mat_ad, mat_bd)

        result = np.concatenate((
            np.concatenate((r_a, r_b), axis=1),
            np.concatenate((r_c, r_d), axis=1)
        ), axis=0)

        # Persist the result


def main():
    # Note, numpy assumes floats by default
    a = np.array((
        [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        [9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0],
        [17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0],
        [25.0, 26.0, 27.0, 28.0, 29.0, 30.0, 31.0, 32.0],
        [33.0, 34.0, 35.0, 36.0, 37.0, 38.0, 39.0, 40.0],
        [41.0, 42.0, 43.0, 44.0, 45.0, 46.0, 47.0, 48.0],
        [49.0, 50.0, 51.0, 52.0, 53.0, 54.0, 55.0, 56.0],
        [57.0, 58.0, 59.0, 60.0, 61.0, 62.0, 63.0, 64.0],
    ))

    b = np.array((
        [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5],
        [9.5, 10.5, 11.5, 12.5, 13.5, 14.5, 15.5, 16.5],
        [17.5, 18.5, 19.5, 20.5, 21.5, 22.5, 23.5, 24.5],
        [25.5, 26.5, 27.5, 28.5, 29.5, 30.5, 31.5, 32.5],
        [33.5, 34.5, 35.5, 36.5, 37.5, 38.5, 39.5, 40.5],
        [41.5, 42.5, 43.5, 44.5, 45.5, 46.5, 47.5, 48.5],
        [49.5, 50.5, 51.5, 52.5, 53.5, 54.5, 55.5, 56.5],
        [57.5, 58.5, 59.5, 60.5, 61.5, 62.5, 63.5, 64.5],
    ))

    expected = np.dot(a, b)

    # Set up the state
    subdivide_matrix_into_state(a, SUBMATRICES_KEY_A)
    subdivide_matrix_into_state(b, SUBMATRICES_KEY_B)

    # Kick off the multiplication on the four quadrants initially
    args_a = np.array([0, 0, 0])
    args_b = np.array([0, 0, 1])
    args_c = np.array([0, 1, 0])
    args_d = np.array([0, 1, 1])

    call_a = chainThisWithInput(1, args_a.tobytes())
    call_b = chainThisWithInput(1, args_b.tobytes())
    call_c = chainThisWithInput(1, args_c.tobytes())
    call_d = chainThisWithInput(1, args_d.tobytes())

    # Load the result
    result = reconstruct_matrix_from_submatrices(RESULT_MATRIX_KEY)

    print("\nEXPECTED\n {}".format(expected))
    print("\nRESULT\n{}".format(result))


if __name__ == "__main__":
    idx = getFunctionIdx()

    if idx == 0:
        main()
    else:
        input_bytes = getInput()
        input_args = np.frombuffer(input_bytes, dtype=int)

        step = input_args[0]
        row = input_args[1]
        col = input_args[2]

        print("Doing multiplication STEP {} ROW {} COL {}".format(step, row, col))
        do_multiplication(step, row, col)

