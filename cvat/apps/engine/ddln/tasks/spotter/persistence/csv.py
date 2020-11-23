from cvat.apps.engine.ddln.tasks.spotter.models import LabeledBoundingBox


def iterate_bboxes(reader):
    for row in reader._reader:
        score, source = None, None
        if len(row) == 8:
            *row, score, source = row
        *points, class_id, track_id = row
        xtl, ytl, xbr, ybr = map(float, points)
        bbox = LabeledBoundingBox.from_two_corners(xtl, ytl, xbr, ybr, class_id, track_id)
        if source:
            bbox.source = source
            bbox.score = score
        yield bbox


def write_bbox(bbox, writer):
    row = (_ff(bbox.left), _ff(bbox.top), _ff(bbox.right), _ff(bbox.bottom), bbox.class_id, bbox.track_id)
    writer._writer.writerow(row)


def _ff(value):
    return "{0:.6f}".format(value)
