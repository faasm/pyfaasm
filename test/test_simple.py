import unittest
from pyfaasm.core import checkPythonBindings


class TestSimple(unittest.TestCase):

    def test_simple_bindings(self):
        # Just check this doesn't error
        checkPythonBindings()
