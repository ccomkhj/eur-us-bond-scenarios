import Plotly from 'plotly.js-dist-min';
import type { Panel } from './data';
import { type Num, rollingCorr, crossCorr, bartlettBand } from './stats';
import { type Mode, prepare } from './transform';

export type { Mode } from './transform';

/**
 * Overlay (always levels): EUR/USD on the left axis; on the right axis the individual
 * US & German yields (solid) PLUS the derived UST-Bund spreads (dashed). Yields and
 * spreads share the right axis because both are in percent / percentage points
 * (roughly 0-5), so the ~4% yields and the ~2 pp gaps read on one scale.
 */
export function renderOverlay(el: HTMLElement, panel: Panel): void {
  const x = panel.dates;
  const yield_ = (key: string, name: string) => ({
    x, y: panel.series[key], name, yaxis: 'y2', type: 'scatter', mode: 'lines',
  });
  const spread = (key: string, name: string) => ({
    x, y: panel.series[key], name, yaxis: 'y2', type: 'scatter', mode: 'lines',
    line: { dash: 'dash' as const },
  });
  const traces = [
    { x, y: panel.series.eurusd, name: 'EUR/USD', yaxis: 'y', type: 'scatter', mode: 'lines', line: { width: 2.5, color: '#111' } },
    yield_('ust10y', 'US 10y'),
    yield_('bund10y', 'DE 10y (Bund)'),
    yield_('ust2y', 'US 2y'),
    yield_('schatz2y', 'DE 2y (Schatz)'),
    spread('spread10y', 'US-DE 10y spread'),
    spread('spread2y', 'US-DE 2y spread'),
  ];
  Plotly.react(el, traces as never, {
    title: 'EUR/USD (left) vs US & German yields and their spreads (right)',
    yaxis: { title: 'EUR/USD' },
    yaxis2: { title: 'yield / spread (%, pp)', overlaying: 'y', side: 'right' },
    legend: { orientation: 'h' },
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
