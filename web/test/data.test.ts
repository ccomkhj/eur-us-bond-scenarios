import { describe, it, expect } from 'vitest';
import { sliceFrom, type Panel } from '../src/data';

const panel: Panel = {
  dates: ['2019-01-01', '2020-01-01', '2021-01-01', '2022-01-01'],
  series: { eurusd: [1.1, 1.12, 1.18, 1.13], spread10y: [2.5, 1.9, 1.5, 2.8] },
};

describe('sliceFrom', () => {
  it('keeps only rows on/after the start date, across all series', () => {
    const s = sliceFrom(panel, '2021-01-01');
    expect(s.dates).toEqual(['2021-01-01', '2022-01-01']);
    expect(s.series.eurusd).toEqual([1.18, 1.13]);
    expect(s.series.spread10y).toEqual([1.5, 2.8]);
  });

  it('returns the whole panel when start is before all dates', () => {
    expect(sliceFrom(panel, '2000-01-01').dates.length).toBe(4);
  });
});
