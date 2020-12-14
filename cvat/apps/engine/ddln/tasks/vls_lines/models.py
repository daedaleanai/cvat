from typing import Optional

from cvat.apps.engine.ddln.geometry import Line


class Runway:
    def __init__(
        self,
        id: str,
        left_line: Optional[Line],
        right_line: Optional[Line],
        center_line: Optional[Line],
        start_line: Optional[Line],
        end_line: Optional[Line],
        designator_line: Optional[Line],
    ):
        self.id = id
        self.left_line = left_line
        self.right_line = right_line
        self.center_line = center_line
        self.start_line = start_line
        self.end_line = end_line
        self.designator_line = designator_line

    @property
    def track_id(self):
        return self.id
