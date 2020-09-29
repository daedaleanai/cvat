import pathlib
import random
import re
from unittest import TestCase

from cvat.apps.engine.ddln.sequences import group, distribute
from cvat.apps.engine.utils import group_on_delimiter, natural_order

sequences_dir = pathlib.Path(__file__).parent / "data" / "sequences"

alice, bob, chris, david, eva = "Alice Bob Chris David Eva".split()


class DistributeSequencesTest(TestCase):
    def test_single_assignee(self):
        chunks = ['A', 'B', 'C']
        assignees = [alice]

        actual = distribute(chunks, assignees)

        self.assertEqual(actual, [
            ('A', [alice]),
            ('B', [None]),
            ('C', [None]),
        ])

    def test_multiple_assignees(self):
        chunks = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        assignees = [alice, bob, chris]

        actual = distribute(chunks, assignees)

        self.assertEqual(actual, [
            ('A', [alice]),
            ('B', [bob]),
            ('C', [chris]),
            ('D', [None]),
            ('E', [None]),
            ('F', [None]),
            ('G', [None]),
            ('H', [None]),
        ])

    def test_multiple_assignees_triple_annotated(self):
        chunks = ['A', 'B']
        assignees = [alice, bob, chris]

        actual = distribute(chunks, assignees, 3)

        self.assertEqual(actual, [
            ('A', [alice, bob, chris]),
            ('B', [alice, bob, chris]),
        ])

    def test_multiple_assignees_double_annotated(self):
        chunks = ['A', 'B', 'C', 'D']
        assignees = [alice, bob, chris]

        actual = distribute(chunks, assignees, 2)

        self.assertEqual(actual, [
            ('A', [alice, bob]),
            ('B', [chris, alice]),
            ('C', [bob, chris]),
            ('D', [alice, bob]),
        ])


class GroupSequencesTest(TestCase):
    def test_cases(self):
        for test_file in sequences_dir.glob("*.txt"):
            with self.subTest(task=test_file.stem):
                sequences, chunk_size, expected = read_case_data(test_file)
                random.shuffle(sequences)

                actual = group(sequences, chunk_size)

                self.assertEqual(_(expected), _(_get_seq_names(actual)))


def read_case_data(test_file):
    content = test_file.read_text()
    input, chunk_size, output = re.split(r'#{3,}\s+(\d+)\s+#{3,}\n', content)
    sequences = [_parse_line(line) for line in input.splitlines()]
    chunk_size = int(chunk_size)
    output = re.sub(r"\s*#.*$", '', output, flags=re.MULTILINE)
    expected = group_on_delimiter(output.splitlines(), '')
    return sequences, chunk_size, expected


def _parse_line(line):
    seq_name, size = line.split('\t')
    size = int(size)
    return seq_name, size


def _get_seq_names(chunks):
    return [[s[0] for s in sequences] for sequences in chunks]


def _(chunks):
    """Ignore order during comparison"""
    chunks = [sorted(sequences, key=natural_order) for sequences in chunks]
    chunks.sort()
    return chunks
