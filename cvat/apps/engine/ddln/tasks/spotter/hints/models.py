# http://wiki.glidernet.org/wiki:ogn-flavoured-aprs
# For ADSB data type is always UNKNOWN
label_by_type = {
    "UNKNOWN": "Unknown",
    "GLIDER": "Fixed wing aircraft",
    "TOWPLANE": "Fixed wing aircraft",
    "HELICOPTER": "Helicopter",
    "PARACHUTE": "Parachute",
    "DROPPLANE": "Fixed wing aircraft",
    "FIXED_HG": "Fixed wing aircraft",
    "SOFT_HG": "Parachute",
    "ENGINE": "Fixed wing aircraft",
    "JET": "Fixed wing aircraft",
    "UFO": "Unknown",
    "BALLOON": "Hot air balloon",
    "AIRSHIP": "Hot air balloon",
    "UAV": "Drone",
    "STATIC": "Unknown",
}

BOX_WIDTH = 100


class Hint:
    def __init__(self, x, y, id, type, distance, vertical_distance, velocity):
        self.x = x
        self.y = y
        self.id = id
        self.type = type
        self.distance = distance  # metres
        self.vertical_distance = vertical_distance  # metres
        self.velocity = velocity  # metres per second

    @property
    def verbose_type(self):
        return label_by_type.get(self.type, 'Unknown')

    def __repr__(self):
        return "Hint({}, {}, {})".format(self.id, self.x, self.y)

    def get_points(self, image_width, image_height):
        center_x = self.x * image_width
        center_y = self.y * image_height
        half = BOX_WIDTH / 2
        # xtl ytl xbr ybr
        return [center_x-half, center_y-half, center_x+half, center_y+half]
