const {
  getMidPoint,
} = require('../../../src/math');

describe("getMidPoint", () => {
  test("correct result for points", () => {
    const a = { x: 0, y: 0 };
    const b = { x: 100, y: 2000 };

    const actual = getMidPoint(a, b);

    expect(actual).toEqual({ x: 50, y: 1000 });
  });

  test("returns the same point for one point", () => {
    const a = { x: 0, y: 0 };

    const actual = getMidPoint(a, a);

    expect(actual).toEqual(a);
  });
});
