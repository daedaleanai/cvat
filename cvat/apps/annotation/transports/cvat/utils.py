from pathlib import PurePath


def parse_frame_name(path):
    image_path = PurePath(path)
    sequence_name = image_path.parents[2].name
    frame_name = image_path.stem
    return frame_name, sequence_name


def build_attrs_dict(shape):
    return {a.name: a.value for a in shape.attributes}
