import unittest

from pyfaasm.core import setState, pushState, pullState, getState, setStateOffset, getStateOffset


class TestState(unittest.TestCase):

    def test_state_read_write(self):
        key = "pyStateTest"
        value_len = 10
        full_value = b'0123456789'
        setState(key, full_value)
        pushState(key)

        # Read state back in
        pullState(key, value_len)
        actual = getState(key, value_len)

        # Check values as expected
        self.assertEqual(full_value, actual)

        # Update a segment
        segment = b'999'
        offset = 2
        segment_len = 3
        modified_value = b'0199956789'
        setStateOffset(key, value_len, offset, segment)

        # Push and pull
        pushState(key)
        pullState(key, value_len)

        # Check full value as expected
        actual = getState(key, value_len)
        self.assertEqual(modified_value, actual)

        # Check getting a segment
        actual_segment = getStateOffset(key, value_len, offset, segment_len)
        self.assertEqual(segment, actual_segment)
