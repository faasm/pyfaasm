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


def set_up_config(matrix_size, n_splits):
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


# Returns the offset of a given submatrix in the overall byte array
def get_submatrix_byte_offset(row_idx, col_idx):
    return (row_idx * MatrixConf.bytes_per_submatrix * MatrixConf.submatrices_per_row) + \
           (col_idx * MatrixConf.bytes_per_submatrix)
