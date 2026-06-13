import { describe, it, expect } from 'vitest';
import { diffs, logReturns } from '../src/stats';
import { pearson, rollingCorr } from '../src/stats';

describe('transforms', () => {
  it('diffs returns first-difference with leading null and null-on-gap', () => {
    expect(diffs([1, 3, null, 4])).toEqual([null, 2, null, null]);
  });

  it('logReturns returns log ratio with leading null', () => {
    const r = logReturns([100, 110]);
    expect(r[0]).toBeNull();
    expect(r[1]).toBeCloseTo(Math.log(110 / 100), 10);
  });

  it('logReturns is null when a value is missing or non-positive', () => {
    expect(logReturns([null, 110])[1]).toBeNull();
    expect(logReturns([0, 110])[1]).toBeNull();
  });
});

describe('correlation', () => {
  it('pearson is 1 for a perfect positive linear relation', () => {
    expect(pearson([1, 2, 3, 4], [2, 4, 6, 8])).toBeCloseTo(1, 10);
  });

  it('pearson drops pairs with a null on either side', () => {
    expect(pearson([1, null, 3, 4], [2, 99, 6, 8])).toBeCloseTo(1, 10);
  });

  it('pearson returns null with fewer than 3 valid pairs', () => {
    expect(pearson([1, 2], [2, 4])).toBeNull();
  });

  it('rollingCorr emits null until the window is full', () => {
    const r = rollingCorr([1, 2, 3, 4], [2, 4, 6, 8], 3);
    expect(r[0]).toBeNull();
    expect(r[1]).toBeNull();
    expect(r[2]).toBeCloseTo(1, 10);
    expect(r[3]).toBeCloseTo(1, 10);
  });
});
