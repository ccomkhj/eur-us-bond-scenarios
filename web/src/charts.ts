import Plotly from 'plotly.js-dist-min';
import type { Panel } from './data';
import { type Num, rollingCorr, crossCorr, bartlettBand } from './stats';
import { type Mode, prepare } from './transform';

export type { Mode } from './transform';

/**
 * Overlay (always levels) as four stacked panels sharing one time axis — avoids
 * cramming different scales (EUR/USD ~1.1, rates ~0-5%, spreads ~2 pp) onto one axis:
 *   - EUR/USD
 *   - market yields: US & German 2y & 10y (%)
 *   - policy rates: Fed funds & ECB deposit rate (%)
 *   - spreads: US-DE 2y & 10y (pp)
 * Country colours are consistent across panels (US = blue, Germany/euro area = orange).
 */
export function renderOverlay(el: HTMLElement, panel: Panel): void {
  const x = panel.dates;
  const US = '#1f77b4';
  const EU = '#ff7f0e';
  const line = (key: string, name: string, axis: string, opts: object = {}) => ({
    x, y: panel.series[key], name, yaxis: axis, type: 'scatter', mode: 'lines', ...opts,
  });
  const traces = [
    line('eurusd', 'EUR/USD', 'y', { line: { width: 2, color: '#111' } }),
    line('ust10y', 'US 10y', 'y2', { line: { color: US } }),
    line('bund10y', 'DE 10y (Bund)', 'y2', { line: { color: EU } }),
    line('ust2y', 'US 2y', 'y2', { line: { color: US, dash: 'dot' } }),
    line('schatz2y', 'DE 2y (Schatz)', 'y2', { line: { color: EU, dash: 'dot' } }),
    line('fed_funds', 'Fed funds', 'y3', { line: { color: US, shape: 'hv' } }),
    line('ecb_rate', 'ECB deposit rate', 'y3', { line: { color: EU, shape: 'hv' } }),
    line('spread10y', 'US-DE 10y spread', 'y4', { line: { color: '#2ca02c' } }),
    line('spread2y', 'US-DE 2y spread', 'y4', { line: { color: '#9467bd' } }),
  ];
  // Taller canvas so four stacked panels stay legible (other charts keep their CSS height).
  el.style.height = '760px';
  Plotly.react(el, traces as never, {
    height: 760,
    title: 'EUR/USD vs US & German yields, policy rates, and spreads (shared time axis)',
    xaxis: { anchor: 'y4', domain: [0, 1] },
    yaxis: { domain: [0.79, 1.0], title: 'EUR/USD' },
    yaxis2: { domain: [0.54, 0.75], title: 'yield (%)' },
    yaxis3: { domain: [0.29, 0.5], title: 'policy (%)' },
    yaxis4: { domain: [0.0, 0.25], title: 'spread (pp)' },
    legend: { orientation: 'h', y: 1.06 },
    hovermode: 'x unified',
    margin: { t: 60 },
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
