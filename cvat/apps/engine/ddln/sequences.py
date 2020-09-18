import itertools

from cvat.apps.engine.utils import natural_order


def group(sequences, chunk_size):
    """Group sequences into chunks of desired size"""
    assert chunk_size > 0
    sequences = sorted(sequences, reverse=True, key=lambda r: natural_order(r[0]))
    result = []

    while sequences:
        current_chunk = [sequences.pop()]
        current_chunk_size = current_chunk[0][1]

        last_element_size = 0
        while sequences and current_chunk_size < chunk_size:
            current_chunk.append(sequences.pop())
            last_element_size = current_chunk[-1][1]
            current_chunk_size += last_element_size

        diff = abs(current_chunk_size - chunk_size)
        diff_no_last_element = abs((current_chunk_size - last_element_size) - chunk_size)

        if diff_no_last_element < diff:
            sequences.append(current_chunk.pop())

        result.append(current_chunk)

    return result


def distribute(chunks, assignees):
    """Distribute chunks between assignees. Leave some chunks unassigned to be picked up by any annotator."""
    assignees = itertools.chain(assignees, itertools.repeat(None))
    return [(ch, a) for ch, a in zip(chunks, assignees)]
