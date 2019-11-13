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


def generate_matrix_conf(matrix_size, n_splits):
    # Remember we're dealing with square matrices and splitting the matrix into
    # four pieces each time we do the divide in the divide and conquer.
    # The number of splits is how many times we're dividing the origin matrices.

    c = MatrixConf()
    c.matrix_size = matrix_size
    c.n_splits = n_splits
    c.bytes_per_matrix = (matrix_size * matrix_size) * NP_ELEMENT_SIZE
    c.submatrices_per_row = 2 ** n_splits
    c.quadrants_per_row = 2 ** (n_splits - 1)
    c.submatrix_size = matrix_size // c.submatrices_per_row
    c.bytes_per_submatrix = (c.submatrix_size * c.submatrix_size) * NP_ELEMENT_SIZE

    return c


# Returns the offset of a given submatrix in the overall byte array
def get_submatrix_byte_offset(conf, row_idx, col_idx):
    return (row_idx * conf.bytes_per_submatrix * conf.submatrices_per_row) + (col_idx * conf.bytes_per_submatrix)


# Gets the key for storing the given quadrant's result
def get_quadrant_key(split_level, row_idx_a, col_idx_a, row_idx_b, col_idx_b):
    key = "matrix_result_split_{}_{}{}{}{}".format(split_level, row_idx_a, col_idx_a, row_idx_b, col_idx_b)
    return key


# Get the total length of a quadrant and the offset for the given quarter
def get_quadrant_len_and_offset(conf, split_level, quarter_idx):
    quadrant_size = conf.matrix_size // (2 * split_level)
    bytes_per_quadrant = (quadrant_size * quadrant_size) * NP_ELEMENT_SIZE

    quarter_size = quadrant_size // 2
    bytes_per_quarter = (quarter_size * quarter_size) * NP_ELEMENT_SIZE
    quarter_offset = quarter_idx * bytes_per_quarter

    return bytes_per_quadrant, quarter_offset, bytes_per_quarter
