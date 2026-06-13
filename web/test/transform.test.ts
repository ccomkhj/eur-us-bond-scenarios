import { describe, it, expect } from 'vitest';
import { prepare } from '../src/transform';

describe('prepare', () => {
  it('levels mode returns the raw series unchanged', () => {
    expect(prepare('eurusd', [1, 2, 3], 'levels')).toEqual([1, 2, 3]);
  });
  it('changes mode uses log-returns for price-like series (eurusd/dxy/brent)', () => {
    const r = prepare('eurusd', [100, 110], 'changes');
    expect(r[0]).toBeNull();
    expect(r[1]).toBeCloseTo(Math.log(110 / 100), 10);
  });
  it('changes mode uses first differences for yields/spreads', () => {
    expect(prepare('spread10y', [2.0, 2.5, 2.1], 'changes')).toEqual([null, 0.5, expect.closeTo(-0.4, 10)]);
  });
});
