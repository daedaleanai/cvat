from abc import abstractmethod, ABC

from ..validation import BaseValidationReporter


class AggregatedCheck(ABC):
    severity = BaseValidationReporter.severity.ERROR
    ignored_values = set()

    @abstractmethod
    def format_message(self, runway_id, value, start, end):
        ...

    def __init__(self, reporter):
        self._reporter = reporter
        self._prev_values = {}
        self._start_frame = {}
        self._end_frame = {}
        self._records = []

    def __setitem__(self, runway_id, value):
        current_frame = self._reporter.frame_name
        prev_value = self._prev_values.get(runway_id)
        if value != prev_value:
            if prev_value is not None:
                self._records.append((runway_id, prev_value, self._start_frame[runway_id], self._end_frame[runway_id]))
            self._start_frame[runway_id] = current_frame
        self._end_frame[runway_id] = current_frame
        self._prev_values[runway_id] = value

    def report(self):
        for runway_id in self._prev_values.keys():
            self[runway_id] = None
        for runway_id, value, start, end in self._records:
            if value in self.ignored_values:
                continue
            message = self.format_message(runway_id, value, start, end)
            self._reporter._report_sequence_message(message, self.severity)


class MissingLateralRaysCheck(AggregatedCheck):
    severity = BaseValidationReporter.severity.WARNING
    ignored_values = {False}

    def format_message(self, runway_id, value, start, end):
        return "{} - {}: Runway {!r} lacks lateral rays".format(start, end, runway_id)


class VisibilityCheck(AggregatedCheck):
    severity = BaseValidationReporter.severity.WARNING
    ignored_values = {(), ("beginning", "designator", "end")}

    def format_message(self, runway_id, value, start, end):
        return "{} - {}: Runway {!r} has invisible lines: {}.".format(start, end, runway_id, ", ".join(value))


def validate(sequences, reporter=None, **kwargs):
    if reporter is None:
        reporter = VlsLinesValidationReporter()
    for seq in sequences:
        reporter.sequence = seq.name
        previous_id = None
        lateral_check = MissingLateralRaysCheck(reporter)
        visibility_check = VisibilityCheck(reporter)

        for frame in seq.frames:
            reporter.frame = frame.name
            reporter.frame_index = frame.index
            reporter.count_frame(seq.name)

            for runway in frame.objects:
                has_lateral_rays = any(line is not None for line in [runway.start_line, runway.end_line, runway.designator_line])
                lateral_check[runway.id] = not has_lateral_rays
                visibility_check[runway.id] = runway.get_invisible_lines()
                current_id = runway.id
                if previous_id and current_id != previous_id:
                    reporter.report_id_changed(previous_id, current_id)
                previous_id = current_id
        lateral_check.report()
        visibility_check.report()
    return reporter


class VlsLinesValidationReporter(BaseValidationReporter):
    object_name = 'Runway'

    def report_unknown_label(self, label):
        self._report("Label {!r} is unknown".format(label), self.severity.WARNING)

    def report_duplicated_rays(self, runway_id, is_lon):
        type = "longitudinal" if is_lon else "lateral"
        self._report("Runway {!r} has duplicated {} rays".format(runway_id, type))

    def report_missing_rays(self, runway_id, is_lon):
        type = "longitudinal" if is_lon else "lateral"
        severity = self.severity.ERROR if is_lon else self.severity.WARNING
        self._report("Runway {!r} lacks {} rays".format(runway_id, type), severity)

    def report_id_changed(self, previous, current):
        self._report("Runway id has changed from {} to {}".format(previous, current))

    def report_lat_disorder(self):
        self._report("Lateral rays are mixed up")

    def report_lon_disorder(self):
        self._report("Longitudinal rays are mixed up")

    def report_wrong_values_amount(self, expected, actual):
        self._report("Wrong values amount. Expected: {}, actual: {}".format(expected, actual))

    def report_not_crossing(self, error):
        self._report("Lines seem not to cross at the same point. Error: {}".format(error))
