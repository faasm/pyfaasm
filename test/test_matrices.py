import unittest

import numpy as np
import redis

from pyfaasm.core import setState
from pyfaasm.matrix import subdivide_matrix_into_state, reconstruct_matrix_from_submatrices, \
    read_submatrix_from_state, divide_and_conquer, RESULT_MATRIX_KEY, write_matrix_params_to_state, \
    load_matrix_conf_from_state, MatrixConf, subdivide_random_matrix_into_state, SUBMATRICES_KEY_A, SUBMATRICES_KEY_B, \
    subdivide_matrix_into_file, reconstruct_matrix_from_file


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

    def test_random_large_matrix_to_state(self):
        subdivide_random_matrix_into_state(self.key)
        actual = reconstruct_matrix_from_submatrices(self.key)

        # Check shape
        self.assertEqual(actual.shape, (MatrixConf.matrix_size, MatrixConf.matrix_size))

    def test_matrix_round_trip(self):
        mat_a = np.random.rand(MatrixConf.matrix_size, MatrixConf.matrix_size)
        subdivide_matrix_into_state(mat_a, self.key)
        actual = reconstruct_matrix_from_submatrices(self.key)

        self.assertTrue(np.array_equal(mat_a, actual))

    def test_matrix_file_round_trip(self):
        mat_a = np.random.rand(MatrixConf.matrix_size, MatrixConf.matrix_size)
        file_path = "/tmp/mat_test"
        subdivide_matrix_into_file(mat_a, file_path)

        actual = reconstruct_matrix_from_file(file_path)
        self.assertTrue(np.array_equal(mat_a, actual))

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
        subdivide_matrix_into_state(mat_a, SUBMATRICES_KEY_A)
        subdivide_matrix_into_state(mat_b, SUBMATRICES_KEY_B)

        # Write result into state
        zero_result = np.zeros((MatrixConf.matrix_size, MatrixConf.matrix_size))
        setState(RESULT_MATRIX_KEY, zero_result.tobytes())

        expected = np.dot(mat_a, mat_b)

        # Invoke the divide and conquer
        divide_and_conquer()

        # Load the result
        actual = reconstruct_matrix_from_submatrices(RESULT_MATRIX_KEY)

        self.assertTrue(np.array_equal(expected, actual))

    def test_distributed_multiplication_with_random(self):
        subdivide_random_matrix_into_state(SUBMATRICES_KEY_A)
        subdivide_random_matrix_into_state(SUBMATRICES_KEY_B)

        mat_a = reconstruct_matrix_from_submatrices(SUBMATRICES_KEY_A)
        mat_b = reconstruct_matrix_from_submatrices(SUBMATRICES_KEY_B)
        expected = np.dot(mat_a, mat_b)

        # Invoke the divide and conquer
        divide_and_conquer()

        # Load the result
        actual = reconstruct_matrix_from_submatrices(RESULT_MATRIX_KEY)

        self.assertTrue(np.array_equal(expected, actual))
