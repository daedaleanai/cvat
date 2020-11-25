const {
  approximateLinesIntersection,
  getLineByTwoPoints,
} = require('../../../src/math');

describe("approximateLinesintersection", () => {
  test("correct result for arbitrary lines", () => {
    const a = getLineByTwoPoints({ x: 0, y: 0 }, { x: 2, y: 1 });
    const b = getLineByTwoPoints({ x: 4, y: 0 }, { x: 5, y: 1 });

    const actual = approximateLinesIntersection([a, b]);

    expect(actual.x).toBeCloseTo(8);
    expect(actual.y).toBeCloseTo(4);
  });

  test("correct result for three arbitrary lines", () => {
    const a = getLineByTwoPoints({ x: 2, y: 4 }, { x: 4, y: 5 });
    const b = getLineByTwoPoints({ x: 1, y: 1 }, { x: 2, y: 2 });
    const c = getLineByTwoPoints({ x: 2, y: -2 }, { x: 4, y: 2 });

    const actual = approximateLinesIntersection([a, b, c]);

    expect(actual.x).toBeCloseTo(6);
    expect(actual.y).toBeCloseTo(6);
  });

  test("correct result for three arbitrary fuzzy lines", () => {
    const a = getLineByTwoPoints({ x: 200, y: 400 }, { x: 400, y: 520 });
    const b = getLineByTwoPoints({ x: 90, y: 100 }, { x: 200, y: 200 });
    const c = getLineByTwoPoints({ x: 200, y: -200 }, { x: 400, y: 180 });

    const actual = approximateLinesIntersection([a, b, c]);

    expect(actual.x).toBeCloseTo(655.67);
    expect(actual.y).toBeCloseTo(662.318);
  });

  test("correct result for vertical line", () => {
    const a = getLineByTwoPoints({ x: 0, y: 1 }, { x: 1, y: 2 });
    const b = getLineByTwoPoints({ x: 3, y: 0 }, { x: 3, y: 8 });

    const actual = approximateLinesIntersection([a, b]);

    expect(actual.x).toBeCloseTo(3);
    expect(actual.y).toBeCloseTo(4);
  });

  test("correct result for horizontal line", () => {
    const a = getLineByTwoPoints({ x: 0, y: 1 }, { x: 1, y: 2 });
    const b = getLineByTwoPoints({ x: 0, y: 5 }, { x: -3, y: 5 });

    const actual = approximateLinesIntersection([a, b]);

    expect(actual.x).toBeCloseTo(4);
    expect(actual.y).toBeCloseTo(5);
  });

  test("returns null for parallel lines", () => {
    const a = getLineByTwoPoints({ x: 0, y: 1 }, { x: 1, y: 2 });
    const b = getLineByTwoPoints({ x: 0, y: 7 }, { x: 1, y: 8 });

    const actual = approximateLinesIntersection([a, b]);

    expect(actual).toBe(null);
  });

  test("returns distant point for fuzzy parallel lines", () => {
    const a = getLineByTwoPoints({ x: 0, y: 1010 }, { x: 1000, y: 2000 });
    const b = getLineByTwoPoints({ x: 0, y: 7000 }, { x: 1000, y: 8000 });

    const actual = approximateLinesIntersection([a, b], 100000);

    expect(actual).toEqual({ x: -599000, y: -592000 });
  });

  test("returns null for the same line", () => {
    const a = getLineByTwoPoints({ x: 0, y: 1 }, { x: 1, y: 2 });

    const actual = approximateLinesIntersection([a, a]);

    expect(actual).toBe(null);
  });
});
