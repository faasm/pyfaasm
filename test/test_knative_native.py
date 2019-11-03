import unittest

from pyfaasm.core import setLocalInputOutput
from pyfaasm.knative_native import handle_message


class TestKnativeNative(unittest.TestCase):
    def setUp(self):
        setLocalInputOutput(True)

    def tearDown(self):
        setLocalInputOutput(False)

    def test_executing_dummy_func(self):
        json_data = {
            "py_user": "dummy_user",
            "py_func": "dummy_echo",
            "input_data": "This is input",
        }

        handle_message(json_data)
