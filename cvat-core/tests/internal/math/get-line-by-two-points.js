const { getLineByTwoPoints } = require('../../../src/math');

describe("getLineByTwoPoints", () => {
  test("returns null for equal points", () => {
    const point = { x: 5, y: 3 };

    const actual = getLineByTwoPoints(point, point);

    expect(actual).toBe(null);
  });

  test("correct result for identity", () => {
    const a = { x: 5, y: 5 };
    const b = { x: 3, y: 3 };

    const actual = getLineByTwoPoints(a, b);

    expect(actual).toEqual({ a: 2, b: -2, c: 0 });
  });

  test("correct result for simple case", () => {
    const a = { x: 0, y: 1 };
    const b = { x: 4, y: 3 };

    const actual = getLineByTwoPoints(a, b);

    expect(actual).toEqual({ a: -2, b: 4, c: -4 });
  });
});
