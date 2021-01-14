from ..models import LabeledBoundingBox, label_by_class_id
from ...utils import build_attrs_dict


def iterate_bboxes(reader):
    if not reader._frame_annotation:
        return
    height = float(reader.image_height)
    width = float(reader.image_width)

    for shape in reader._frame_annotation.labeled_shapes:
        if shape.type != "rectangle":
            # only bounding box is supported
            continue
        if shape.label == "Hint":
            continue

        attrs = build_attrs_dict(shape)

        class_id = attrs.get("Object_class", "")
        track_id = attrs.get("Track_id", "")
        score = attrs.get("Score")
        source = attrs.get("Source")

        xtl, ytl, xbr, ybr = map(float, shape.points)
        xtl = xtl / width
        ytl = ytl / height
        xbr = xbr / width
        ybr = ybr / height

        bbox = LabeledBoundingBox.from_two_corners(xtl, ytl, xbr, ybr, class_id, track_id)
        if source:
            bbox.source = source
            bbox.score = score
        yield bbox


def write_bbox(bbox: LabeledBoundingBox, writer):
    width = writer.image_width
    height = writer.image_height

    xtl = float(bbox.left) * width
    ytl = float(bbox.top) * height
    xbr = float(bbox.right) * width
    ybr = float(bbox.bottom) * height

    attributes = [
        writer._annotations.Attribute(name="Object_class", value=bbox.class_id),
        writer._annotations.Attribute(name="Track_id", value=bbox.track_id),
    ]

    if bbox.score:
        attributes.append(writer._annotations.Attribute(name="Score", value=bbox.score))
    if bbox.source:
        attributes.append(writer._annotations.Attribute(name="Source", value=bbox.source))

    shape = {
        "attributes": attributes,
        "points": [xtl, ytl, xbr, ybr],
        "frame": writer._frame_id,
        "group": 0,
        "z_order": 0,
        "occluded": False,
        "type": "rectangle",
        "label": label_by_class_id[bbox.class_id],
    }
    writer._annotations.add_shape(writer._annotations.LabeledShape(**shape))
