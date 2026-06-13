import { type Num, diffs, logReturns } from './stats';

export type Mode = 'changes' | 'levels';

// Price-like series use log-returns; yields/spreads use first differences.
const LOG_RETURN_SERIES = new Set(['eurusd', 'dxy', 'brent']);

/**
 * Series prepared for statistics given the mode:
 * - 'levels': raw series as-is (correlation here is often spurious — for teaching contrast).
 * - 'changes': log-returns for price-like series, first differences for yields/spreads.
 */
export function prepare(name: string, xs: Num[], mode: Mode): Num[] {
  if (mode === 'levels') return xs;
  return (LOG_RETURN_SERIES.has(name) ? logReturns : diffs)(xs);
}
