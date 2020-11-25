const { Matrix, solve: leastSquaresMethod } = require("ml-matrix");

function findVanishingPoint(lineSegments, infinityDistance) {
  // find the vanishing point and update line segments to intersect
  // exactly at the vanishing point. If vanishing point cannot be found
  // (parallel lines), segments are updated to be exactly parallel
  const segmentCenters = lineSegments.map((s) => getMidPoint(s[0], s[1]));
  const lines = lineSegments.map((s) => getLineByTwoPoints(s[0], s[1]));
  let vanishingPoint = approximateLinesIntersection(lines);
  if (vanishingPoint && !isFinite(vanishingPoint, infinityDistance)) {
    vanishingPoint = null;
  }
  let adjustedLines;
  if (vanishingPoint) {
    adjustedLines = segmentCenters.map((center) =>
      getLineByTwoPoints(center, vanishingPoint)
    );
  } else {
    const angleFactor = approximateAngleFactor(lines);
    adjustedLines = segmentCenters.map((point) =>
      buildLineThrough(point, angleFactor)
    );
  }
  const adjustedLineSegments = lineSegments.map((s, i) => [
    projectOntoLine(s[0], adjustedLines[i]),
    projectOntoLine(s[1], adjustedLines[i])
  ]);
  return [adjustedLineSegments, vanishingPoint];
}

function updateSegment(previous, next, vanishingPoint) {
    const [prevA, prevB] = previous;
    const [nextA, nextB] = next;

    if (vanishingPoint) {
        if (!arePointsEqual(prevA, nextA)) {
            const line = getLineByTwoPoints(vanishingPoint, nextA);
            const newB = projectOntoLine(prevB, line);
            return [nextA, newB];
        } else if (!arePointsEqual(prevB, nextB)) {
            const line = getLineByTwoPoints(vanishingPoint, nextB);
            const newA = projectOntoLine(prevA, line);
            return [newA, nextB];
        }
        return next;
    }

    let line = getLineByTwoPoints(prevA, prevB);
    if (!arePointsEqual(prevA, nextA)) {
        line = buildLineThrough(nextA, line);
        const newB = projectOntoLine(prevB, line);
        return [nextA, newB];
    } else if (!arePointsEqual(prevB, nextB)) {
        line = buildLineThrough(nextB, line);
        const newA = projectOntoLine(prevA, line);
        return [nextA, newA];
    }
    return next;
}

function arePointsEqual(first, second) {
    return Math.abs(first.x - second.x) < 0.001 && Math.abs(first.y - second.y) < 0.001;
}

function pullSegment(point, previousEdges, nextEdges) {
  const [previousStart, previousEnd] = previousEdges;
  const [nextStart, nextEnd] = nextEdges;
  const [ratioX, lengthX] = _calcRatio(previousStart.x, point.x, previousEnd.x);
  const [ratioY, lengthY] = _calcRatio(previousStart.y, point.y, previousEnd.y);
  // The bigger length is, the less relative error is, the more precise ratio is
  let ratio = Math.abs(lengthX) > Math.abs(lengthY) ? ratioX : ratioY;
  if (!Number.isFinite(ratio)) {
    ratio = 0.5;
  }
  const x = _calcCoordinate(nextStart.x, nextEnd.x, ratio);
  const y = _calcCoordinate(nextStart.y, nextEnd.y, ratio);
  return { x, y };
}

function _calcRatio(start, value, end) {
  const offset = value - start;
  const length = end - start;
  const ratio = offset / length;
  return [ratio, length];
}

function _calcCoordinate(start, end, ratio) {
  const length = end - start;
  const offset = length * ratio;
  const value = start + offset;
  return value;
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

function isFinite(point, infinityDistance) {
  const { x, y } = point;
  if (!infinityDistance) return true;
  return Math.max(Math.abs(x), Math.abs(y)) < infinityDistance;
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
  if (line.a === 0 && line.b === 0 && line.c === 0) {
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
  pullSegment,
  updateSegment,
  findVanishingPoint
};
