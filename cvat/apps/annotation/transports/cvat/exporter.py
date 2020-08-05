from cvat.apps.annotation.structures import label_by_class_id
from .utils import parse_frame_name


class CVATExporter:
    def __init__(self, annotations):
        self._annotations = annotations
        self._frame_id_by_names = self._build_frame_id_mapping(annotations)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def begin_frame(self, frame_name, sequence_name):
        frame_id = self._frame_id_by_names[frame_name, sequence_name]
        return CVATFrameWriter(self._annotations, frame_id)

    def _build_frame_id_mapping(self, annotations):
        assert annotations._frame_step == 1
        return {
            parse_frame_name(f.name): f.frame
            for f in annotations.group_by_frame(omit_empty_frames=False)
        }


class CVATFrameWriter:
    def __init__(self, annotations, frame_id):
        self._annotations = annotations
        self._frame_id = frame_id

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def write_bbox(self, bbox):
        width = self._annotations._frame_info[self._frame_id]["width"]
        height = self._annotations._frame_info[self._frame_id]["height"]

        xtl = float(bbox.xtl) * width
        ytl = float(bbox.ytl) * height
        xbr = float(bbox.xbr) * width
        ybr = float(bbox.ybr) * height

        attributes = [
            self._annotations.Attribute(name="Object_class", value=bbox.class_id),
            self._annotations.Attribute(name="Track_id", value=bbox.track_id),
        ]

        if bbox.score:
            attributes.append(self._annotations.Attribute(name="Score", value=bbox.score))
        if bbox.source:
            attributes.append(self._annotations.Attribute(name="Source", value=bbox.source))

        shape = {
            "attributes": attributes,
            "points": [xtl, ytl, xbr, ybr],
            "frame": self._frame_id,
            "group": 0,
            "z_order": 0,
            "occluded": False,
            "type": "rectangle",
            "label": label_by_class_id[bbox.class_id],
        }
        self._annotations.add_shape(self._annotations.LabeledShape(**shape))
