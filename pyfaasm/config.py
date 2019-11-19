# NOTE: we are assuming numpy floats are 8 bytes here
NP_ELEMENT_SIZE = 8

SUBMATRICES_KEY_A = "submatrices_a"
SUBMATRICES_KEY_B = "submatrices_b"
RESULT_MATRIX_KEY = "result_matrix"
MATRIX_CONF_STATE_KEY = "matrix_state"


# Remember we're dealing with square matrices and splitting the matrix into
# four pieces each time we do the divide in the divide and conquer.
# The number of splits is how many times we're dividing the origin matrices.

class MatrixConf(object):
    def __init__(self, matrix_size, n_splits):
        self.matrix_size = matrix_size
        self.n_splits = n_splits
        self.bytes_per_matrix = (matrix_size * matrix_size) * NP_ELEMENT_SIZE

    def get_submatrices_per_row(self, split_level):
        """
        Number of submatrices in a row at the given split level
        """
        return 2 * split_level

    def get_submatrix_size(self, split_level):
        return self.matrix_size / (2 * split_level)

    def get_bytes_per_submatrix(self, split_level):
        sm_size = self.get_submatrix_size(split_level)
        return sm_size * sm_size * NP_ELEMENT_SIZE

    def get_submatrix_byte_offset(self, split_level, row_idx, col_idx):
        """
        Returns the offset of a given submatrix in the overall byte array
        """
        sm_bytes = self.get_bytes_per_submatrix(split_level)
        sm_per_row = 2 * split_level
        return (row_idx * sm_bytes * sm_per_row) + (col_idx * sm_bytes)

    def get_intermediate_result_key(self, split_level, row_a, col_a, row_b, col_b):
        """
        Gets the key for storing an intermediate result
        """
        key = "matrix_result_split_{}_{}{}{}{}".format(split_level, row_a, col_a, row_b, col_b)
        return key

    def get_parent_intermediate_result_key(self, split_level, row_a, col_a, row_b, col_b):
        """
        Gets the key for storing the parent intermediate result
        """
        # Use integer division to get parent quadrant
        parent_row_a = row_a // 2
        parent_col_a = col_a // 2
        parent_row_b = row_b // 2
        parent_col_b = col_b // 2

        parent_split_level = split_level - 1

        return self.get_intermediate_result_key(parent_split_level, parent_row_a, parent_col_a, parent_row_b,
                                                parent_col_b)

    def get_intermediate_result_size(self, split_level):
        """
        Size of the intermediate result
        """
        submatrix_size = self.matrix_size // (2 * (split_level + 1))
        result_len = 8 * (submatrix_size * submatrix_size) * NP_ELEMENT_SIZE

        return result_len

    def get_intermediate_result_offset(self, split_level, quarter_idx):
        sm_size = self.matrix_size // (2 * split_level)
        sm_bytes = (sm_size * sm_size) * NP_ELEMENT_SIZE
        offset = quarter_idx * sm_bytes

        return offset, sm_bytes
