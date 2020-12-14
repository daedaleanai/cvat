from unittest import TestCase

from cvat.apps.engine.ddln.geometry import Point, Line
from cvat.apps.engine.ddln.tasks.vls_lines.persistence.csv import as_row, from_row

# tests fail for now due to rounding on export ( distance = format(distance, ".3f") )
WIDTH = HEIGHT = 100
TEST_CASES = (
    (Point(0, 0), Point(100, 0), 1, 180),
    (Point(100, 0), Point(100, 100), 1, 90),
    (Point(100, 100), Point(0, 100), 1, 0),
    (Point(0, 100), Point(0, 0), 1, 270),

    (Point(0, 0), Point(100, 100), 0, 135),
    (Point(100, 0), Point(0, 100), 0, 45),
    (Point(50, 0), Point(50, 100), 0, 90),
    (Point(0, 50), Point(100, 50), 0, 0),

    (Point(50, 0), Point(0, 50), 0.70710678, 225),
    (Point(0, 50), Point(50, 100), 0.70710678, 315),

    (Point(50, 0), Point(100, 50), 0.70710678, 135),
    (Point(100, 50), Point(50, 100), 0.70710678, 45),
)


class SerializeTest(TestCase):
    def test_serialize_invisible(self):
        angle, distance = as_row(None, WIDTH, HEIGHT)

        self.assertEqual(angle, '')
        self.assertEqual(distance, '')

    def test_deserialize_invisible(self):
        line = from_row(['', ''], WIDTH, HEIGHT)

        self.assertIsNone(line)

    def test_normalization(self):
        for a, b, expected_distance, expected_angle in TEST_CASES:
            with self.subTest(a=a, b=b):
                first = Line.by_two_points(a, b)
                second = Line.by_two_points(b, a)

                self.assertEqual(first, second)

    def test_serialization(self):
        for a, b, expected_distance, expected_angle in TEST_CASES:
            for to_reverse in [True, False]:
                with self.subTest(a=a, b=b, reversed=to_reverse):
                    line = Line.by_two_points(b, a) if to_reverse else Line.by_two_points(a, b)

                    angle, distance = as_row(line, WIDTH, HEIGHT)

                    self.assertEqual(angle, expected_angle)
                    self.assertAlmostEqual(distance, expected_distance)

    def test_deserialization(self):
        for a, b, expected_distance, expected_angle in TEST_CASES:
            for to_reverse in [False]:
                with self.subTest(a=a, b=b, reversed=to_reverse):
                    first = Line.by_two_points(b, a) if to_reverse else Line.by_two_points(a, b)

                    angle, distance = as_row(first, WIDTH, HEIGHT)
                    second = from_row([str(angle), str(distance)], WIDTH, HEIGHT)

                    self.assertEqual(first, second)
