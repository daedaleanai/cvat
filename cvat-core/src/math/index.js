const { Matrix, solve: leastSquaresMethod } = require("ml-matrix");

function findVanishingPoint(lineSegments, thresholdAngle) {
  // find the vanishing point and update line segments to intersect
  // exactly at the vanishing point.
  // If the angle between any two line segments is greater than thresholdAngle,
  // the lines are considered to intersect at a finite point,
  // otherwise the lines are considered to intersect at an infinite point (to be parallel).
  const lines = lineSegments.map((s) => getLineByTwoPoints(s[0], s[1]));
  let vanishingPoint = approximateLinesIntersection(lines);
  if (vanishingPoint) {
    lineSegments = lineSegments.map(([a, b]) => {
      if (pointsDistance(b, vanishingPoint) < pointsDistance(a, vanishingPoint)) {
        return [a, b];
      }
      return [b, a];
    });
  }
  // use the end of line which is far from the vanishing point, as its position is more precise
  // than the position of the other end
  const anchorPoints = lineSegments.map((s) => s[0]);
  if (vanishingPoint && !isFinite(vanishingPoint, anchorPoints, thresholdAngle)) {
    vanishingPoint = null;
  }
  let adjustedLines;
  if (vanishingPoint) {
    adjustedLines = anchorPoints.map((anchor) =>
      getLineByTwoPoints(anchor, vanishingPoint)
    );
  } else {
    const angleFactor = approximateAngleFactor(lines);
    adjustedLines = anchorPoints.map((point) =>
      buildLineThrough(point, angleFactor)
    );
  }
  const adjustedLineSegments = lineSegments.map((s, i) => [
    projectOntoLine(s[0], adjustedLines[i]),
    projectOntoLine(s[1], adjustedLines[i])
  ]);
  return [adjustedLineSegments, vanishingPoint];
}

function toPolarCoordinates(point, rotationPoint = null) {
    if (rotationPoint) {
        point = { x: point.x - rotationPoint.x, y: point.y - rotationPoint.y };
    }
    const { x, y } = point;
    const r = Math.sqrt(x*x + y*y);
    const phi = Math.atan2(y, x);
    return { r, phi };
}

function fromPolarCoordinates(point, rotationPoint = null) {
    const { r, phi } = point;
    let x = r * Math.cos(phi);
    let y = r * Math.sin(phi);
    if (rotationPoint) {
        x += rotationPoint.x;
        y += rotationPoint.y;
    }
    return { x, y };
}

function getOppositeAngle(phi) {
    const d = Math.PI * 2;
    return (d + phi) % d - Math.PI;
}

function getAngleBetween(alpha, beta) {
    const d = Math.PI * 2;
    const diff = Math.abs(alpha - beta) % d;
    return diff < Math.PI ? diff : d - diff;
}

function getAngle(line) {
    return Math.atan2(-line.a, line.b);
}

function rotate(point, phi) {
    const { x, y } = point;
    return {
        x: x * Math.cos(phi) + y * Math.sin(phi),
        y: -x * Math.sin(phi) + y * Math.cos(phi),
    };
}

function pointsDistance(first, second) {
    return Math.sqrt(Math.pow(second.y - first.y, 2) + Math.pow(second.x - first.x, 2));
}

function arePointsEqual(first, second) {
    return pointsDistance(first, second) < 0.001;
}

function approximateLinesIntersection(lines) {
  const a = new Matrix(lines.map((line) => [line.a, line.b]));
  const b = Matrix.columnVector(lines.map((line) => -line.c));
  try {
    const res = leastSquaresMethod(a, b);
    const x = res.get(0, 0);
    const y = res.get(1, 0);
    return { x, y };
  } catch (error) {
    // lines are parallel
    return null;
  }
}

function approximateAngleFactor(lines) {
  // find the angle factor for fuzzy parallel lines
  const N = lines.length;
  let sumA = 0;
  let sumB = 0;
  lines.forEach((line) => {
    let { a, b } = line;
    const q = Math.max(Math.abs(a), Math.abs(b));
    a /= q;
    b /= q;
    if (a < 0) {
      a = -a;
      b = -b;
    }
    sumA += a;
    sumB += b;
  });
  const a = sumA / N;
  const b = sumB / N;
  return { a, b };
}

function isFinite(vanishingPoint, points, thresholdAngle) {
  if (!thresholdAngle) return true;
  const angles = points.map(p => toPolarCoordinates(p, vanishingPoint).phi);
  let maxAngle = 0;
  for (let i = 0; i < angles.length - 1; i++) {
    for (let j = i + 1; j < angles.length; j++) {
      const a = getAngleBetween(angles[i], angles[j]);
      maxAngle = Math.max(maxAngle, a);
    }
  }
  return maxAngle > thresholdAngle;
}

function getMidPoint(first, second) {
  const x = first.x + (second.x - first.x) / 2;
  const y = first.y + (second.y - first.y) / 2;
  return { x, y };
}

function buildLineThrough(point, angleFactor) {
  const { x, y } = point;
  const { a, b } = angleFactor;
  const c = -(a * x + b * y);
  return { a, b, c };
}

function getLineByTwoPoints(first, second) {
  const line = {
    a: first.y - second.y,
    b: second.x - first.x,
    c: first.x * second.y - second.x * first.y
  };
  if (Math.abs(line.a) < Number.EPSILON && Math.abs(line.b) < Number.EPSILON) {
    return null;
  }
  return line;
}

function projectOntoLine(point, line) {
  const norm = {
    a: -line.b,
    b: line.a,
    c: line.b * point.x - line.a * point.y
  };
  return intersectLines(line, norm);
}

function intersectLines(first, second) {
  const divisor = first.a * second.b - second.a * first.b;
  if (Math.abs(divisor) < Number.EPSILON) {
    return null;
  }
  const x = (first.b * second.c - second.b * first.c) / divisor;
  const y = (second.a * first.c - first.a * second.c) / divisor;
  return { x, y };
}

module.exports = {
  intersectLines,
  projectOntoLine,
  getLineByTwoPoints,
  approximateLinesIntersection,
  approximateAngleFactor,
  arePointsEqual,
  getMidPoint,
  findVanishingPoint,
  toPolarCoordinates,
  fromPolarCoordinates,
  getOppositeAngle,
  getAngleBetween,
  getAngle,
  rotate,
  pointsDistance
};
