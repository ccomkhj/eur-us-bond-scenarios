import Plotly from 'plotly.js-dist-min';
import type { Panel } from './data';
import { type Num, diffs, logReturns, rollingCorr, crossCorr, bartlettBand } from './stats';

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

/** Overlay: EUR/USD on the left axis, the 10y & 2y spreads on the right axis (always levels). */
export function renderOverlay(el: HTMLElement, panel: Panel): void {
  const x = panel.dates;
  const traces = [
    { x, y: panel.series.eurusd, name: 'EUR/USD', yaxis: 'y', type: 'scatter', mode: 'lines' },
    { x, y: panel.series.spread10y, name: 'UST-Bund 10y', yaxis: 'y2', type: 'scatter', mode: 'lines' },
    { x, y: panel.series.spread2y, name: 'UST-Schatz 2y', yaxis: 'y2', type: 'scatter', mode: 'lines' },
  ];
  Plotly.react(el, traces as never, {
    title: 'EUR/USD vs yield spreads (levels)',
    yaxis: { title: 'EUR/USD' },
    yaxis2: { title: 'spread (pp)', overlaying: 'y', side: 'right' },
    margin: { t: 40 },
  } as never);
}

/** Lead-lag: cross-correlation of EUR/USD vs 10y-spread, with a Bartlett significance band. */
export function renderLeadLag(el: HTMLElement, panel: Panel, maxLag: number, mode: Mode): void {
  const fx = prepare('eurusd', panel.series.eurusd ?? [], mode);
  const sp = prepare('spread10y', panel.series.spread10y ?? [], mode);
  // x = spread, y = fx -> a positive peak lag means the spread leads FX.
  const cc = crossCorr(sp, fx, maxLag);
  const n = fx.filter((v) => v != null).length;
  const band = bartlettBand(n);
  const shapes = Number.isFinite(band)
    ? [band, -band].map((yv) => ({
        type: 'line', x0: -maxLag, x1: maxLag, y0: yv, y1: yv,
        line: { dash: 'dot', width: 1, color: '#999' },
      }))
    : [];
  Plotly.react(
    el,
    [{ x: cc.map((c) => c.lag), y: cc.map((c) => c.corr), type: 'bar', name: 'corr' }] as never,
    {
      title: `Lead-lag: spread vs EUR/USD (${mode}). Positive lag = spread leads FX`,
      xaxis: { title: 'lag (days)' },
      yaxis: { title: 'correlation', range: [-1, 1] },
      shapes,
      margin: { t: 40 },
    } as never,
  );
}

/** Rolling correlation of EUR/USD vs 10y-spread over time. */
export function renderRollingCorr(el: HTMLElement, panel: Panel, windowDays: number, mode: Mode): void {
  const fx = prepare('eurusd', panel.series.eurusd ?? [], mode);
  const sp = prepare('spread10y', panel.series.spread10y ?? [], mode);
  const rc = rollingCorr(fx, sp, windowDays);
  Plotly.react(
    el,
    [{ x: panel.dates, y: rc, type: 'scatter', mode: 'lines', name: `rolling ${windowDays}d` }] as never,
    {
      title: `Rolling correlation (${windowDays}d): EUR/USD vs 10y spread (${mode})`,
      yaxis: { title: 'correlation', range: [-1, 1] },
      margin: { t: 40 },
    } as never,
  );
}
