import itertools
import heapq as hq

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
    """Distribute chunks between assignees"""
    if times_assigned == 1:
        return _distribute_single_annotation(chunks, assignees)
    else:
        return _distribute_multiannotation(chunks, assignees, times_assigned)


def _distribute_multiannotation(chunks, assignees, times_assigned=1):
    """Assign in round-robin manner, so annotators won't assign sequences manually
    and won't make mistakes by assigning the same sequence multiple times to the same annotator.
    """
    # if the assertions aren't met, an annotator might be assigned multiple times to the same chunk
    assert len(assignees) == len(set(assignees))
    assert len(assignees) >= times_assigned
    assignees_pool = itertools.cycle(assignees)
    groups = (list(gr) for gr in grouper(assignees_pool, times_assigned))
    return list(zip(chunks, groups))


def _distribute_single_annotation(chunks, assignees):
    """Each assignee gets no more than 1 chunk,
    extra chunks are left unassigned, so any annotator can pick them up.
    """
    assignees_pool = itertools.chain(assignees, itertools.repeat(None))
    groups = ([a] for a in assignees_pool)
    return list(zip(chunks, groups))


def extend_assignees(sequences_data, assignees):
    """Assign one extra annotator to each sequence.

    Make sure that an annotator is not assigned to the sequence he/she has worked on.
    Preferably, distribute workload evenly among assignees.
    """
    assignments = []
    failed_sequences = []
    # order is required because user instances are not comparable,
    # when two users have the same amount of workload, next value in tuple is compared
    priority_queue = [(0, order, a) for order, a in enumerate(assignees)]
    hq.heapify(priority_queue)
    for sequence, sequence_length, performers in sequences_data:
        workload, order, candidate = _find_candidate(priority_queue, performers)
        if not candidate:
            failed_sequences.append(sequence)
            continue
        assignments.append((sequence, candidate))
        workload += sequence_length
        hq.heappush(priority_queue, (workload, order, candidate))
    return assignments, failed_sequences


def _find_candidate(priority_queue, performers):
    backup = []
    success = False
    while priority_queue:
        workload, order, candidate = hq.heappop(priority_queue)
        if candidate not in performers:
            success = True
            break
        backup.append((workload, order, candidate))

    for item in backup:
        hq.heappush(priority_queue, item)

    if not success:
        return None, None, None
    # if more than 1 assignee could be added to the same sequence,
    # the candidate would have to be added to the performers
    # performers.add(candidate)
    return workload, order, candidate
