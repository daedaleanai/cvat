from ..models import RunwayPoint, Runway


def iterate_runways(reader):
    for row in reader._reader:
        runway_id, full_visible, *pts_data = row
        full_visible = bool(int(full_visible))
        assert len(pts_data) == 18  # 6 points, each point having 3 values
        start_left, start_right = _from_row(pts_data[0:3]), _from_row(pts_data[3:6])
        end_left, end_right = _from_row(pts_data[6:9]), _from_row(pts_data[9:12])
        threshold_left, threshold_right = _from_row(pts_data[12:15]), _from_row(pts_data[15:18])
        yield Runway(runway_id, full_visible, start_left, start_right, end_left, end_right, threshold_left, threshold_right)


def write_runway(runway, writer):
    writer._writer.writerow((
        runway.id,
        int(runway.full_visible),
        *_as_row(runway.start_left),
        *_as_row(runway.start_right),
        *_as_row(runway.end_left),
        *_as_row(runway.end_right),
        *_as_row(runway.threshold_left),
        *_as_row(runway.threshold_right),
    ))


def _from_row(row):
    visible, x, y = row
    visible = bool(int(visible))
    x = _deserialize(x)
    y = _deserialize(y)
    return RunwayPoint(visible, x, y)


def _as_row(point):
    return int(point.visible), _serialize(point.x), _serialize(point.y)


def _serialize(coordinate):
    return '' if coordinate is None else coordinate


def _deserialize(input):
    return None if input == '' else int(input)
