import unittest
from json import dumps

import numpy as np
import redis

from pyfaasm.config import RESULT_MATRIX_KEY
from pyfaasm.core import setState, setEmulatorMessage
from pyfaasm.matrix import subdivide_matrix_into_state, reconstruct_matrix_from_submatrices, \
    read_submatrix_from_state, divide_and_conquer, write_matrix_params_to_state, \
    load_matrix_conf_from_state, subdivide_random_matrix_into_state, SUBMATRICES_KEY_A, SUBMATRICES_KEY_B
from pyfaasm.matrix_data import subdivide_matrix_into_file, reconstruct_matrix_from_file


class TestMatrices(unittest.TestCase):
    def setUp(self):
        self.redis = redis.Redis()
        self.redis.flushall()

        self.key = "matrix_tester"

        msg = {
            "user": "python",
            "function": "py_func",
            "py_user": "python",
            "py_func": "mat_mul",
        }
        msg_json = dumps(msg)
        setEmulatorMessage(msg_json)

        # Write and read config
        write_matrix_params_to_state(1000, 3)
        self.conf = load_matrix_conf_from_state()

        self.assertEqual(self.conf.matrix_size, 1000)
        self.assertEqual(self.conf.n_splits, 3)

    def test_random_large_matrix_to_state(self):
        subdivide_random_matrix_into_state(self.conf, self.key)
        actual = reconstruct_matrix_from_submatrices(self.conf, self.key)

        # Check shape
        self.assertEqual(actual.shape, (self.conf.matrix_size, self.conf.matrix_size))

    def test_matrix_round_trip(self):
        mat_a = np.random.rand(self.conf.matrix_size, self.conf.matrix_size)
        subdivide_matrix_into_state(self.conf, mat_a, self.key)
        actual = reconstruct_matrix_from_submatrices(self.conf, self.key)

        self.assertTrue(np.array_equal(mat_a, actual))

    def test_matrix_file_round_trip(self):
        mat_a = np.random.rand(self.conf.matrix_size, self.conf.matrix_size)
        file_path = "/tmp/mat_test"
        subdivide_matrix_into_file(self.conf, mat_a, file_path)

        actual = reconstruct_matrix_from_file(self.conf, file_path)
        self.assertTrue(np.array_equal(mat_a, actual))

    def test_reading_submatrix_from_state(self):
        mat_a = np.random.rand(self.conf.matrix_size, self.conf.matrix_size)
        subdivide_matrix_into_state(self.conf, mat_a, self.key)
        row_idx = 3
        col_idx = 4

        # Get the submatrix directly from the original
        row_start = row_idx * self.conf.submatrix_size
        col_start = col_idx * self.conf.submatrix_size
        expected = mat_a[
                   row_start:row_start + self.conf.submatrix_size,
                   col_start:col_start + self.conf.submatrix_size,
                   ]

        actual = read_submatrix_from_state(self.conf, self.key, row_idx, col_idx)

        self.assertTrue(np.array_equal(expected, actual))

    def test_distributed_multiplication(self):
        # Set up the problem
        mat_a = np.random.rand(self.conf.matrix_size, self.conf.matrix_size)
        mat_b = np.random.rand(self.conf.matrix_size, self.conf.matrix_size)
        subdivide_matrix_into_state(self.conf, mat_a, SUBMATRICES_KEY_A)
        subdivide_matrix_into_state(self.conf, mat_b, SUBMATRICES_KEY_B)

        # Write result into state
        zero_result = np.zeros((self.conf.matrix_size, self.conf.matrix_size))
        setState(RESULT_MATRIX_KEY, zero_result.tobytes())

        expected = np.dot(mat_a, mat_b)

        # Invoke the divide and conquer
        divide_and_conquer()

        # Load the result
        actual = reconstruct_matrix_from_submatrices(self.conf, RESULT_MATRIX_KEY)

        self.assertTrue(np.array_equal(expected, actual))

    def test_distributed_multiplication_with_random(self):
        subdivide_random_matrix_into_state(self.conf, SUBMATRICES_KEY_A)
        subdivide_random_matrix_into_state(self.conf, SUBMATRICES_KEY_B)

        mat_a = reconstruct_matrix_from_submatrices(self.conf, SUBMATRICES_KEY_A)
        mat_b = reconstruct_matrix_from_submatrices(self.conf, SUBMATRICES_KEY_B)
        expected = np.dot(mat_a, mat_b)

        # Invoke the divide and conquer
        divide_and_conquer()

        # Load the result
        actual = reconstruct_matrix_from_submatrices(self.conf, RESULT_MATRIX_KEY)

        self.assertTrue(np.array_equal(expected, actual))
