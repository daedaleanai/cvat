const {
  pullSegment
} = require('../../../src/math');

describe("pullSegment", () => {
  test("correct result", () => {
    const point = { x: 75, y: 0 };
    const previousEdges = [
      { x: 0, y: 0 },
      { x: 100, y: 0 }
    ];
    const nextEdges = [
      { x: 0, y: 0 },
      { x: 100, y: 100 }
    ];

    const actual = pullSegment(point, previousEdges, nextEdges);

    expect(actual).toEqual({ x: 75, y: 75 });
  });

  test("correct result for outlier point", () => {
    const point = { x: 150, y: 150 };
    const previousEdges = [
      { x: 0, y: 0 },
      { x: 100, y: 100 }
    ];
    const nextEdges = [
      { x: 0, y: 0 },
      { x: 20, y: 40 }
    ];

    const actual = pullSegment(point, previousEdges, nextEdges);

    expect(actual).toEqual({ x: 30, y: 60 });
  });

  test("correct result for reverse outlier point", () => {
    const point = { x: 150, y: 150 };
    const previousEdges = [
      { x: 0, y: 0 },
      { x: -100, y: -100 }
    ];
    const nextEdges = [
      { x: 0, y: 0 },
      { x: -20, y: -40 }
    ];

    const actual = pullSegment(point, previousEdges, nextEdges);

    expect(actual).toEqual({ x: 30, y: 60 });
  });
});
