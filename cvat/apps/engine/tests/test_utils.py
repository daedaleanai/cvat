from unittest import TestCase

from cvat.apps.engine.utils import find_range


def is_not_zero(value):
    return value != 0


class FindRangeTest(TestCase):
    def test_simple_case(self):
        actual = find_range([0, 0, 1, 1, 0], is_not_zero)

        self.assertEqual(actual, (2, 4))

    def test_single_element(self):
        actual = find_range([0, 0, 1, 0], is_not_zero)

        self.assertEqual(actual, (2, 3))

    def test_single_element_at_end(self):
        actual = find_range([0, 0, 1], is_not_zero)

        self.assertEqual(actual, (2, 3))

    def test_no_tail(self):
        actual = find_range([0, 0, 1, 1], is_not_zero)

        self.assertEqual(actual, (2, 4))

    def test_no_range(self):
        actual = find_range([0, 0, 0, 0], is_not_zero)

        self.assertEqual(actual, (-1, -1))

    def test_empty(self):
        actual = find_range([], is_not_zero)

        self.assertEqual(actual, (-1, -1))
