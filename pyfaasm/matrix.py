import numpy as np
from numpy import int32

from pyfaasm.config import MATRIX_CONF_STATE_KEY, SUBMATRICES_KEY_A, SUBMATRICES_KEY_B, \
    get_submatrix_byte_offset, NP_ELEMENT_SIZE, generate_matrix_conf, get_quadrant_key, \
    get_quadrant_len_and_offset
from pyfaasm.core import setState, getStateOffset, getState, chainThisWithInput, awaitCall, setStateOffset, \
    registerFunction
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


# This is the distributed worker that will be invoked by faasm
def distributed_divide_and_conquer(input_bytes):
    conf = load_matrix_conf_from_state()

    input_args = np.frombuffer(input_bytes, dtype=int32)

    split_level = input_args[0]
    quarter_idx = input_args[1]
    row_idx_a = input_args[2]
    col_idx_a = input_args[3]
    row_idx_b = input_args[4]
    col_idx_b = input_args[5]

    # If we're at the target number of splits, do the work
    if split_level == conf.n_splits:
        # Read in the relevant submatrices of each input matrix
        mat_a = read_submatrix_from_state(conf, SUBMATRICES_KEY_A, row_idx_a, col_idx_a)
        mat_b = read_submatrix_from_state(conf, SUBMATRICES_KEY_B, row_idx_b, col_idx_b)

        # Do the multiplication in memory
        result = np.dot(mat_a, mat_b)
    else:
        # Recursively kick off more divide and conquer
        result = chain_multiplications(conf, split_level, row_idx_a, col_idx_a, row_idx_b, col_idx_b)

    # Write the result
    bytes_per_quadrant, quarter_offset, _ = get_quadrant_len_and_offset(conf, split_level, quarter_idx)
    state_key = get_quadrant_key(split_level, row_idx_a, col_idx_a, row_idx_b, col_idx_b)

    # Set the result
    setStateOffset(state_key, bytes_per_quadrant, quarter_offset, result.tobytes())


def divide_and_conquer():
    conf = load_matrix_conf_from_state()
    print("Running divide and conquer for {}x{} matrix with {} splits".format(
        conf.matrix_size,
        conf.matrix_size,
        conf.n_splits
    ))

    # To keep things working in native python
    registerFunction(1, distributed_divide_and_conquer)

    # Kick off the basic multiplication jobs
    return chain_multiplications(conf, 0, 0, 0, 0, 0)


def chain_multiplications(conf, split_level, row_idx_a, col_idx_a, row_idx_b, col_idx_b):
    call_ids = []

    # Spawn 8 workers to do the relevant multiplications
    next_split_level = split_level + 1

    next_row_idx_a = 2 * row_idx_a
    next_row_idx_b = 2 * row_idx_b
    next_col_idx_a = 2 * col_idx_a
    next_col_idx_b = 2 * col_idx_b

    # Multiplications expressed as offsets from top left of each matrix
    multiplications = [
        # A11.B11 + A12.B21 | A11.B12 + A12.B22
        [(0, 0, 0, 0), (0, 1, 1, 0)], [(0, 0, 0, 1), (0, 1, 1, 1)],
        # A21.B11 + A22.B21 | A21.B12 + A22.B22
        [(1, 0, 0, 0), (1, 1, 1, 0)], [(1, 0, 0, 1), (1, 1, 1, 1)],
    ]

    # For each quarter, kick off the two multiplications (8 calls in total)
    for quarter_idx, mult_one, mult_two in enumerate(multiplications):
        # First call
        inputs_a = np.array([
            next_split_level,
            quarter_idx,
            next_row_idx_a + mult_one[0], next_col_idx_a + mult_one[1],
            next_row_idx_b + mult_one[2], next_col_idx_b + mult_one[3],
        ])

        call_ids.append(chainThisWithInput(1, inputs_a.tobytes()))

        # Second call
        inputs_b = np.array([
            next_split_level,
            quarter_idx + 1,
            next_row_idx_a + mult_two[0], next_col_idx_a + mult_two[1],
            next_row_idx_b + mult_two[2], next_col_idx_b + mult_two[3],
        ])

        call_ids.append(chainThisWithInput(1, inputs_b.tobytes()))

    # Await completion
    for call_id in call_ids:
        awaitCall(call_id)

    # Read the full results for this quadrant
    state_key = get_quadrant_key(split_level, row_idx_a, col_idx_a, row_idx_b, col_idx_b)
    bytes_per_quadrant, quarter_offset, bytes_per_quarter = get_quadrant_len_and_offset(conf, split_level, 0)
    quadrant_result = getState(state_key, bytes_per_quadrant)

    quarters = []
    for i in [0, 2, 4, 6]:
        offset_a = bytes_per_quarter * i
        offset_b = bytes_per_quarter * (i + 1)
        r_a = np.frombuffer(quadrant_result[offset_a:offset_a + bytes_per_quarter])
        r_b = np.frombuffer(quadrant_result[offset_b:offset_b + bytes_per_quarter])

        # Actually do the addition of the matrices
        quarters.append(r_a + r_b)

    # Reconstitute the result
    result = np.concatenate((
        np.concatenate((quarters[0], quarters[1]), axis=1),
        np.concatenate((quarters[2], quarters[3]), axis=1)
    ), axis=0)

    return result
