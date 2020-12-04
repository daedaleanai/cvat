const {
  findVanishingPoint,
} = require('../../../src/math');

describe("findVanishingPoint", () => {
  test("correct result", () => {
    const segments = [
      [
        { x: 0, y: 0 },
        { x: 2010, y: 970 }
      ],
      [
        { x: 5000, y: 0 },
        { x: 6020, y: 1020 }
      ]
    ];

    const [newSegments, vanishingPoint] = findVanishingPoint(segments, 100000);

    expect(vanishingPoint).toEqual({
      x: 9663.461538461537,
      y: 4663.461538461538
    });
    expect(newSegments).not.toEqual(segments);
  });

  test("correct result for parallel lines", () => {
    const segments = [
      [
        { x: 0, y: 0 },
        { x: 2010, y: 2000 }
      ],
      [
        { x: 0, y: 1000 },
        { x: 5000, y: 6020 }
      ]
    ];

    const [newSegments, vanishingPoint] = findVanishingPoint(segments, 100000);

    expect(vanishingPoint).toBeNull();
    expect(newSegments).not.toEqual(segments);
  });
});
