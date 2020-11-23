from ..validation import BaseValidationReporter


def validate(sequences, reporter=None, **kwargs):
    if reporter is None:
        reporter = VlsValidationReporter()
    for seq in sequences:
        for frame in seq.frames:
            reporter.count_frame(seq.name)
    return reporter


class VlsValidationReporter(BaseValidationReporter):
    object_name = 'Runway'

    def report_inconsistent_visibility(self, violators):
        if not violators:
            return
        violators = (p.replace('_', ' ') for p in violators)
        self._report("Runway is visible, but its {} points are not".format(', '.join(violators)))

    def report_likely_full_visible(self):
        message = "All runway's points are visible but the runway is not (possibly should be visible too)"
        self._report(message, self.severity.WARNING)
