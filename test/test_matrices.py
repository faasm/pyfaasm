import unittest

import numpy as np
import redis

from pyfaasm.matrix import subdivide_matrix_into_state, reconstruct_matrix_from_submatrices, \
    read_submatrix_from_state, divide_and_conquer, RESULT_MATRIX_KEY, write_matrix_params_to_state, \
    load_matrix_conf_from_state, MatrixConf


class TestMatrices(unittest.TestCase):
    def setUp(self):
        self.redis = redis.Redis()
        self.redis.flushall()

        self.key = "matrix_tester"

        # Write and read config
        write_matrix_params_to_state(1000, 3)
        load_matrix_conf_from_state()
        self.assertEqual(MatrixConf.matrix_size, 1000)
        self.assertEqual(MatrixConf.n_splits, 3)

    def test_matrix_round_trip(self):
        mat_a = np.random.rand(MatrixConf.matrix_size, MatrixConf.matrix_size)
        subdivide_matrix_into_state(mat_a, self.key)
        reconstruct_matrix_from_submatrices(self.key)

    def test_reading_submatrix_from_state(self):
        mat_a = np.random.rand(MatrixConf.matrix_size, MatrixConf.matrix_size)
        subdivide_matrix_into_state(mat_a, self.key)
        row_idx = 3
        col_idx = 4

        # Get the submatrix directly from the original
        row_start = row_idx * MatrixConf.submatrix_size
        col_start = col_idx * MatrixConf.submatrix_size
        expected = mat_a[
                   row_start:row_start + MatrixConf.submatrix_size,
                   col_start:col_start + MatrixConf.submatrix_size,
                   ]

        actual = read_submatrix_from_state(self.key, row_idx, col_idx)

        self.assertTrue(np.array_equal(expected, actual))

    def test_distributed_multiplication(self):
        # Set up the problem
        mat_a = np.random.rand(MatrixConf.matrix_size, MatrixConf.matrix_size)
        mat_b = np.random.rand(MatrixConf.matrix_size, MatrixConf.matrix_size)

        expected = np.dot(mat_a, mat_b)

        # Invoke the divide and conquer
        divide_and_conquer()

        # Load the result
        actual = reconstruct_matrix_from_submatrices(RESULT_MATRIX_KEY)

        self.assertTrue(np.array_equal(expected, actual))
