import unittest

import numpy as np
import redis

from pyfaasm.matrix import subdivide_matrix_into_state, reconstruct_matrix_from_submatrices, MATRIX_SIZE, \
    read_submatrix_from_state, SUBMATRIX_SIZE, divide_and_conquer, RESULT_MATRIX_KEY, SUBMATRICES_PER_ROW


class TestMatrices(unittest.TestCase):
    def setUp(self):
        self.redis = redis.Redis()
        self.redis.flushall()

        self.key = "matrix_tester"

    def test_matrix_round_trip(self):
        mat_a = np.random.rand(MATRIX_SIZE, MATRIX_SIZE)
        subdivide_matrix_into_state(mat_a, self.key)
        reconstruct_matrix_from_submatrices(self.key)

    def test_reading_submatrix_from_state(self):
        mat_a = np.random.rand(MATRIX_SIZE, MATRIX_SIZE)
        subdivide_matrix_into_state(mat_a, self.key)
        row_idx = 3
        col_idx = 4

        # Get the submatrix directly from the original
        row_start = row_idx * SUBMATRIX_SIZE
        col_start = col_idx * SUBMATRIX_SIZE
        expected = mat_a[
                   row_start:row_start + SUBMATRIX_SIZE,
                   col_start:col_start + SUBMATRIX_SIZE,
                   ]

        actual = read_submatrix_from_state(self.key, row_idx, col_idx)

        self.assertTrue(np.array_equal(expected, actual))

    def test_distributed_multiplication(self):
        # Set up the problem
        mat_a = np.random.rand(MATRIX_SIZE, MATRIX_SIZE)
        mat_b = np.random.rand(MATRIX_SIZE, MATRIX_SIZE)

        expected = np.dot(mat_a, mat_b)

        # Invoke the divide and conquer
        divide_and_conquer()

        # Load the result
        actual = reconstruct_matrix_from_submatrices(RESULT_MATRIX_KEY)

        self.assertTrue(np.array_equal(expected, actual))
