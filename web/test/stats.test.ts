import { describe, it, expect } from 'vitest';
import { diffs, logReturns } from '../src/stats';

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
