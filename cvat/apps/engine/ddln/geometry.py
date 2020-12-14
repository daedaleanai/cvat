import math

D = math.pi * 2
ABS_TOL = 1e-12


def get_angle_between(alpha, beta):
    """Get closest angle between alpha and beta in range [0, pi]"""
    diff = get_counterclockwise_angle(alpha, beta)
    return diff if diff <= math.pi else D - diff


def get_counterclockwise_angle(alpha, beta):
    """Get counterclockwise angle from alpha to beta in range [0, 2pi)"""
    return (beta - alpha) % D


def get_opposite_angle(alpha):
    return (D + alpha) % D - math.pi


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return "Point(x={}, y={})".format(self.x, self.y)

    def __sub__(self, other):
        assert isinstance(other, Point)
        return Point(self.x - other.x, self.y - other.y)

    def __add__(self, other):
        assert isinstance(other, Point)
        return Point(self.x + other.x, self.y + other.y)

    def rotate(self, phi):
        x = self.x * math.cos(phi) + self.y * math.sin(phi)
        y = -self.x * math.sin(phi) + self.y * math.cos(phi)
        return Point(x, y)

    def distance_to(self, other):
        if isinstance(other, Point):
            return math.sqrt((other.x - self.x) ** 2 + (other.y - self.y) ** 2)
        elif isinstance(other, Line):
            # also have to divide by sqrt(a**2 + b**2), but due to normalization in
            # Line constructor it is equal to 1
            return abs(other.a * self.x + other.b * self.y + other.c)
            # alternative implementation:
            #     projection = self.project_onto(other)
            #     return self.distance_to(projection)
        raise TypeError("cannot calculate distance from Point to {}".format(type(other)))

    def get_mid_point(self, other):
        assert isinstance(other, Point)
        x = self.x + (other.x - self.x) / 2
        y = self.y + (other.y - self.y) / 2
        return Point(x, y)

    def project_onto(self, line):
        c = line.b * self.x - line.a * self.y
        norm = Line(-line.b, line.a, c)
        return line.intersect(norm)

    def to_polar_coordinates(self, rotation_point=None):
        point = self - rotation_point if rotation_point else self
        r = math.sqrt(point.x ** 2 + point.y ** 2)
        phi = math.atan2(point.y, point.x)
        return PolarPoint(r, phi)


class PolarPoint:
    def __init__(self, r, phi):
        self.r = r
        self.phi = phi

    def __repr__(self):
        return "PolarPoint(r={}, phi={})".format(self.r, self.phi)

    def to_cartesian_coordinates(self, rotation_point=None):
        x = self.r * math.cos(self.phi)
        y = self.r * math.sin(self.phi)
        point = Point(x, y)
        if rotation_point:
            point += rotation_point
        return point


class Line:
    def __init__(self, a, b, c):
        if math.isclose(a, 0, abs_tol=ABS_TOL) and math.isclose(b, 0, abs_tol=ABS_TOL):
            # both a and b cannot be equal to zero.
            # in this case if c > 0, that's non-existent line,
            # otherwise it's any point of the space
            raise ValueError("Invalid line")
        factor = -1 if a < 0 else 1
        factor /= math.sqrt(a ** 2 + b ** 2)
        self.a = a * factor
        self.b = b * factor
        self.c = c * factor
        if math.isclose(self.a, 0, abs_tol=ABS_TOL) and self.b < 0:
            self.a *= -1
            self.b *= -1
            self.c *= -1

    def __repr__(self):
        return "Line(a={}, b={}, c={})".format(self.a, self.b, self.c)

    def __eq__(self, other):
        return (
            isinstance(other, Line)
            and math.isclose(self.a, other.a, abs_tol=ABS_TOL)
            and math.isclose(self.b, other.b, abs_tol=ABS_TOL)
            and math.isclose(self.c, other.c, abs_tol=ABS_TOL)
        )

    @classmethod
    def by_two_points(cls, first, second):
        a = first.y - second.y
        b = second.x - first.x
        c = first.x * second.y - second.x * first.y
        return cls(a, b, c)

    @classmethod
    def by_point_and_angle(cls, point, phi):
        if math.isclose(get_angle_between(phi, math.pi / 2), 0, abs_tol=ABS_TOL):
            b = 0
            a = -1
        else:
            b = 1
            a = - math.tan(phi)
        c = -(a * point.x + b * point.y)
        return cls(a, b, c)

    def get_angle(self):
        return math.atan2(-self.a, self.b)

    def intersect(self, other):
        divisor = self.a * other.b - other.a * self.b
        if math.isclose(divisor, 0, abs_tol=ABS_TOL):
            # lines are parallel
            return None
        x = (self.b * other.c - other.b * self.c) / divisor
        y = (other.a * self.c - self.a * other.c) / divisor
        return Point(x, y)
