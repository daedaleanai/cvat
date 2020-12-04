const {
  getLineByTwoPoints,
  intersectLines,
} = require('../../../src/math');

describe("intersectLines", () => {
  test("correct result for arbitrary lines", () => {
    const a = getLineByTwoPoints({ x: 0, y: 0 }, { x: 2, y: 1 });
    const b = getLineByTwoPoints({ x: 4, y: 0 }, { x: 5, y: 1 });

    const actual = intersectLines(a, b);

    expect(actual).toEqual({ x: 8, y: 4 });
  });

  test("correct result for vertical line", () => {
    const a = getLineByTwoPoints({ x: 0, y: 1 }, { x: 1, y: 2 });
    const b = getLineByTwoPoints({ x: 3, y: 0 }, { x: 3, y: 8 });

    const actual = intersectLines(a, b);

    expect(actual).toEqual({ x: 3, y: 4 });
  });

  test("correct result for horizontal line", () => {
    const a = getLineByTwoPoints({ x: 0, y: 1 }, { x: 1, y: 2 });
    const b = getLineByTwoPoints({ x: 0, y: 5 }, { x: -3, y: 5 });

    const actual = intersectLines(a, b);

    expect(actual).toEqual({ x: 4, y: 5 });
  });

  test("returns null for parallel lines", () => {
    const a = getLineByTwoPoints({ x: 0, y: 1 }, { x: 1, y: 2 });
    const b = getLineByTwoPoints({ x: 0, y: 7 }, { x: 1, y: 8 });

    const actual = intersectLines(a, b);

    expect(actual).toBe(null);
  });

  test("returns null for the same line", () => {
    const a = getLineByTwoPoints({ x: 0, y: 1 }, { x: 1, y: 2 });

    const actual = intersectLines(a, a);

    expect(actual).toBe(null);
  });
});
