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
