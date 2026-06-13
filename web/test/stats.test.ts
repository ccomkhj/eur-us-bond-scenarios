import { describe, it, expect } from 'vitest';
import { diffs, logReturns } from '../src/stats';
import { pearson, rollingCorr } from '../src/stats';
import { crossCorr, bartlettBand } from '../src/stats';

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

  it('diffs and logReturns return [] for empty input', () => {
    expect(diffs([])).toEqual([]);
    expect(logReturns([])).toEqual([]);
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

  it('pearson returns null for a constant series (zero variance)', () => {
    expect(pearson([5, 5, 5, 5], [1, 2, 3, 4])).toBeNull();
  });

  it('rollingCorr emits null until the window is full', () => {
    const r = rollingCorr([1, 2, 3, 4], [2, 4, 6, 8], 3);
    expect(r[0]).toBeNull();
    expect(r[1]).toBeNull();
    expect(r[2]).toBeCloseTo(1, 10);
    expect(r[3]).toBeCloseTo(1, 10);
  });
});

describe('lead-lag', () => {
  it('crossCorr peaks at the lag by which x leads y', () => {
    // x leads y by 1 step: y[t] = x[t-1]. Use non-linear data so only lag=1 peaks.
    const x = [1, 3, 2, 5, 4, 7, 6, 8];
    const y = [0, 1, 3, 2, 5, 4, 7, 6];
    const cc = crossCorr(x, y, 3);
    const peak = cc.reduce((best, c) => ((c.corr ?? -2) > (best.corr ?? -2) ? c : best));
    expect(peak.lag).toBe(1);
    expect(peak.corr).toBeCloseTo(1, 10);
    expect(cc[0]!.lag).toBe(-3);
    expect(cc[cc.length - 1]!.lag).toBe(3);
  });

  it('bartlettBand is 2/sqrt(n)', () => {
    expect(bartlettBand(100)).toBeCloseTo(0.2, 10);
  });

  it('bartlettBand returns NaN for n <= 0', () => {
    expect(Number.isNaN(bartlettBand(0))).toBe(true);
  });
});

describe('lead-lag negative branch', () => {
  it('crossCorr peaks at a negative lag when y leads x', () => {
    // x_t = y_{t-1}: y leads x by 1, so corr(x_t, y_{t+lag}) peaks at lag = -1.
    const y = [1, 3, 2, 5, 4, 7, 6, 8];
    const x = [0, 1, 3, 2, 5, 4, 7, 6];
    const cc = crossCorr(x, y, 3);
    const peak = cc.reduce((best, c) => ((c.corr ?? -2) > (best.corr ?? -2) ? c : best));
    expect(peak.lag).toBe(-1);
    expect(peak.corr).toBeCloseTo(1, 10);
  });
});
