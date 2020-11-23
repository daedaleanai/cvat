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
