import unittest
from pyfaasm.core import checkPythonBindings, setState, pushState, pullState, getState, setStateOffset, getStateOffset
import numpy as np


class TestNumpySerailization(unittest.TestCase):

    def test_reading_and_writing_matrix(self):
        mat_a = np.array([0, 1, 2], [3, 4, 5], [4, 5, 6])
