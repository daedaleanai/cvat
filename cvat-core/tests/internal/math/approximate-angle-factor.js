const {
  approximateAngleFactor,
  getLineByTwoPoints,
} = require('../../../src/math');

describe("approximateAngleFactor", () => {
  test("correct result for parallel lines", () => {
    const a = getLineByTwoPoints({ x: 0, y: 0 }, { x: 1, y: 1 });
    const b = getLineByTwoPoints({ x: 0, y: 1 }, { x: 1, y: 2 });

    const actual = approximateAngleFactor([a, b]);

    expect(actual).toEqual({ a: 1, b: -1 });
  });

  test("correct result for opposite lines", () => {
    const a = getLineByTwoPoints({ x: 0, y: 0 }, { x: 1, y: 1 });
    const b = getLineByTwoPoints({ x: 1, y: 1 }, { x: 0, y: 0 });

    const actual = approximateAngleFactor([a, b]);

    expect(actual).toEqual({ a: 1, b: -1 });
  });

  test("correct result for fuzzy lines", () => {
    const a = getLineByTwoPoints({ x: 0, y: 0 }, { x: 1, y: 2 });
    const b = getLineByTwoPoints({ x: 0, y: 0 }, { x: 2, y: 1 });

    const actual = approximateAngleFactor([a, b]);

    expect(actual).toEqual({ a: 0.75, b: -0.75 });
  });
});
