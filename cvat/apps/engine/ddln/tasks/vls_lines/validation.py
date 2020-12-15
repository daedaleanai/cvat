from ..validation import BaseValidationReporter


def validate(sequences, reporter=None, **kwargs):
    if reporter is None:
        reporter = VlsLinesValidationReporter()
    for seq in sequences:
        for frame in seq.frames:
            reporter.count_frame(seq.name)
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

    def report_lat_disorder(self):
        self._report("Lateral rays are mixed up")

    def report_lon_disorder(self):
        self._report("Longitudinal rays are mixed up")
