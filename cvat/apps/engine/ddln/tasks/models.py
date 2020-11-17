class Sequence:
    def __init__(self, name, frames=None):
        if frames is None:
            frames = []
        self.name = name
        self.frames = frames


class Frame:
    def __init__(self, name, objects):
        self.name = name
        self.index = None
        self.objects = objects
        self.object_by_track_id = {b.track_id: b for b in objects}

    def __repr__(self):
        return 'Frame<{}>'.format(self.name)
