from cvat.apps.annotation.structures import label_by_class_id
from cvat.apps.annotation.transports.cvat.utils import parse_frame_name


def add_bbox(bbox, frame_id, annotations):
    width = annotations._frame_info[frame_id]["width"]
    height = annotations._frame_info[frame_id]["height"]

    xtl = float(bbox.xtl) * width
    ytl = float(bbox.ytl) * height
    xbr = float(bbox.xbr) * width
    ybr = float(bbox.ybr) * height

    attributes = [
        annotations.Attribute(name="Object_class", value=bbox.class_id),
        annotations.Attribute(name="Track_id", value=bbox.track_id),
    ]

    if bbox.score:
        attributes.append(annotations.Attribute(name="Score", value=bbox.score))
    if bbox.source:
        attributes.append(annotations.Attribute(name="Source", value=bbox.source))

    shape = {
        "attributes": attributes,
        "points": [xtl, ytl, xbr, ybr],
        "frame": frame_id,
        "group": 0,
        "z_order": 0,
        "occluded": False,
        "type": "rectangle",
        "label": label_by_class_id[bbox.class_id],
    }
    annotations.add_shape(annotations.LabeledShape(**shape))


def build_frame_id_mapping(annotations):
    assert annotations._frame_step == 1
    return {
        parse_frame_name(f.name): f.frame
        for f in annotations.group_by_frame(omit_empty_frames=False)
    }


