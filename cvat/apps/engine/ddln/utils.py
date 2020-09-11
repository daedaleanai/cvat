from pathlib import PurePath


def parse_frame_name(path):
    image_path = PurePath(path)
    if len(image_path.parents) < 3:
        return path, ''
    sequence_name = image_path.parents[2].name
    frame_name = image_path.stem
    return frame_name, sequence_name


class FrameContainer:
    # both start_frame and stop_frame are inclusive,
    # but boundary is exclusive (i.e. boundary = end_frame + 1)
    def __init__(self, ranges):
        frame_set = set()
        boundaries = []
        for start_frame, stop_frame in ranges:
            boundaries.append(stop_frame + 1)
            segment_frames = range(start_frame, stop_frame + 1)
            frame_set = frame_set.union(segment_frames)
        boundaries.sort()
        self._frame_set = frame_set
        self._boundaries = boundaries

    @classmethod
    def for_jobs(cls, jobs):
        return cls((job.segment.start_frame, job.segment.stop_frame) for job in jobs)

    def contains(self, frame):
        return frame in self._frame_set

    def get_closest_boundary(self, frame):
        for b in self._boundaries:
            if b > frame:
                return b
        raise ValueError("Frame '{}' is greater than any boundary".format(frame))
