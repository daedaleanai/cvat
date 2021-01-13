class HintWriter:
    def __init__(self, exporter, current_sequence):
        self._exporter = exporter
        self._track_by_id = {}
        self._sequence = current_sequence
        self.can_have_hints = any(label.name == 'Hint' for label in self._exporter._annotations._label_mapping.values())

    def write(self, hint, frame, sequence_name):
        if not self.can_have_hints:
            return
        frame_id = self._exporter._frame_id_by_names.get((frame, sequence_name))
        if frame_id is None:
            return
        annotations = self._exporter._annotations
        image_width = annotations._frame_info[frame_id]["width"]
        image_height = annotations._frame_info[frame_id]["height"]
        track = self._track_by_id.setdefault(hint.id, annotations.Track(label='Hint', group=0, shapes=[]))
        attributes = [
            annotations.Attribute(name="Id", value=hint.id),
            annotations.Attribute(name="Aircraft_type", value=hint.verbose_type),
            annotations.Attribute(name="Raw_type", value=hint.type),
            annotations.Attribute(name="Distance_m", value=str(hint.distance)),
            annotations.Attribute(name="Height_diff_m", value=str(hint.vertical_distance)),
            annotations.Attribute(name="Velocity_mps", value=str(hint.velocity)),
        ]
        shape = annotations.TrackedShape(
            frame=frame_id,
            points=hint.get_points(image_width, image_height),
            attributes=attributes,
            outside=False,
            keyframe=True,
            type='rectangle',
            occluded=False,
            z_order=0,
        )
        track.shapes.append(shape)

    def finish(self):
        for track in self._track_by_id.values():
            self._close_interpolation(track.shapes)
            self._exporter._annotations.add_track(track)

    def _close_interpolation(self, shapes):
        last_shape = shapes[-1]
        if (last_shape.frame + 1, self._sequence) not in self._exporter._frame_id_by_names:
            shapes.pop()
            last_shape = shapes[-1]
        shapes.append(self._exporter._annotations.TrackedShape(
            frame=last_shape.frame + 1,
            points=last_shape.points.copy(),
            attributes=last_shape.attributes.copy(),
            outside=True,
            keyframe=True,
            type='rectangle',
            occluded=False,
            z_order=0,
        ))
