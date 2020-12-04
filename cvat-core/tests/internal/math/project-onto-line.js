const {
  getLineByTwoPoints,
  projectOntoLine,
} = require('../../../src/math');

describe("projectOntoLine", () => {
  test("correct result for arbitrary point", () => {
    const point = { x: 0, y: 4 };
    const line = getLineByTwoPoints({ x: 0, y: 0 }, { x: 1, y: 1 });

    const actual = projectOntoLine(point, line);

    expect(actual).toEqual({ x: 2, y: 2 });
  });

  test("correct result for mirrored point", () => {
    const point = { x: 4, y: 0 };
    const line = getLineByTwoPoints({ x: 0, y: 0 }, { x: 1, y: 1 });

    const actual = projectOntoLine(point, line);

    expect(actual).toEqual({ x: 2, y: 2 });
  });

  test("returns the same point when it lies on the line", () => {
    const point = { x: 2, y: 4 };
    const line = getLineByTwoPoints({ x: 0, y: 0 }, { x: 1, y: 2 });

    const actual = projectOntoLine(point, line);

    expect(actual).toEqual({ x: 2, y: 4 });
  });
});
