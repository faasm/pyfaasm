import unittest
from json import dumps

from parameterized import parameterized

from pyfaasm.core import setLocalInputOutput, \
    setEmulatorMessage, getOutput, setOutput, PYTHON_LOCAL_OUTPUT


class TestEmulator(unittest.TestCase):
    original_local_output = False

    @classmethod
    def setUpClass(cls):
        # Check what local output already set to
        cls.original_local_output = PYTHON_LOCAL_OUTPUT

    @classmethod
    def tearDownClass(cls):
        # Reset to original local output value
        setLocalInputOutput(cls.original_local_output)

    def test_local_output(self):
        setLocalInputOutput(True)

        # Set up the function
        msg = {
            "user": "python",
            "function": "py_func",
            "py_user": "python",
            "py_func": "echo",
        }
        json_msg = dumps(msg)
        setEmulatorMessage(json_msg)

        # Check output is initially empty
        self.assertIsNone(getOutput())

        # Set output and check
        output_a = b'12345'
        setOutput(output_a)
        self.assertEqual(getOutput(), output_a)

        # Set output again and check updated
        output_b = b'666777'
        setOutput(output_b)
        self.assertEqual(getOutput(), output_b)

    def test_changing_function_clears_local_output(self):
        setLocalInputOutput(True)

        # Set output and check
        output_a = b'12345'
        setOutput(output_a)
        self.assertEqual(getOutput(), output_a)

        # Change function
        msg = {
            "user": "foo",
            "function": "bar",
        }
        json_msg = dumps(msg)
        setEmulatorMessage(json_msg)

        # Check output is now empty
        self.assertIsNone(getOutput())
