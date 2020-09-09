import itertools

from cvat.apps.engine.utils import natural_order, grouper


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


def distribute(chunks, assignees, times_assigned=1):
    """Distribute chunks between assignees

    If times assigned is equal to 1, each assignee gets no more than 1 chunk,
    extra chunks are left unassigned, so any annotator can pick them up.

    If times assigned is greater than 1, assign in round-robin manner, so annotators won't assign sequences manually
    and won't make mistakes by assigning the same sequence multiple times to the same annotator.
    """
    # if the assertions aren't met, an annotator might be assigned multiple times to the same chunk
    assert times_assigned == 1 or len(assignees) == len(set(assignees))
    assert times_assigned == 1 or len(assignees) >= times_assigned
    if times_assigned == 1:
        assignees_pool = itertools.chain(assignees, itertools.repeat(None))
        groups = ([a] for a in assignees_pool)
    else:
        assignees_pool = itertools.cycle(assignees)
        groups = (list(gr) for gr in grouper(assignees_pool, times_assigned))

    return list(zip(chunks, groups))
