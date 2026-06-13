export type Num = number | null;

/** First difference. Leading element is null; any gap (null on either side) yields null. */
export function diffs(xs: Num[]): Num[] {
  const out: Num[] = [null];
  for (let i = 1; i < xs.length; i++) {
    const a = xs[i - 1];
    const b = xs[i];
    out.push(a != null && b != null ? b - a : null);
  }
  return out;
}

/** Log returns. Leading element null; null when either value is missing or non-positive. */
export function logReturns(xs: Num[]): Num[] {
  const out: Num[] = [null];
  for (let i = 1; i < xs.length; i++) {
    const a = xs[i - 1];
    const b = xs[i];
    out.push(a != null && b != null && a > 0 && b > 0 ? Math.log(b / a) : null);
  }
  return out;
}

/** Pearson correlation over pairwise-complete observations. Null if < 3 valid pairs. */
export function pearson(xs: Num[], ys: Num[]): number | null {
  const xv: number[] = [];
  const yv: number[] = [];
  const n = Math.min(xs.length, ys.length);
  for (let i = 0; i < n; i++) {
    const a = xs[i];
    const b = ys[i];
    if (a != null && b != null && Number.isFinite(a) && Number.isFinite(b)) {
      xv.push(a);
      yv.push(b);
    }
  }
  const m = xv.length;
  if (m < 3) return null;
  const mx = xv.reduce((s, v) => s + v, 0) / m;
  const my = yv.reduce((s, v) => s + v, 0) / m;
  let sxy = 0;
  let sxx = 0;
  let syy = 0;
  for (let i = 0; i < m; i++) {
    const dx = xv[i]! - mx;
    const dy = yv[i]! - my;
    sxy += dx * dy;
    sxx += dx * dx;
    syy += dy * dy;
  }
  const denom = Math.sqrt(sxx * syy);
  return denom === 0 ? null : sxy / denom;
}

/** Trailing rolling Pearson correlation; null until `window` points are available. */
export function rollingCorr(xs: Num[], ys: Num[], window: number): (number | null)[] {
  const out: (number | null)[] = [];
  for (let i = 0; i < xs.length; i++) {
    if (i + 1 < window) {
      out.push(null);
      continue;
    }
    out.push(pearson(xs.slice(i + 1 - window, i + 1), ys.slice(i + 1 - window, i + 1)));
  }
  return out;
}

export interface LagCorr {
  lag: number;
  corr: number | null;
}

/**
 * Cross-correlation of x and y over lags [-maxLag, maxLag].
 * corr at lag L = pearson(x_t, y_{t+L}). A positive peak lag means **x leads y**
 * by that many steps. Inputs should already be changes/returns, not levels.
 */
export function crossCorr(xs: Num[], ys: Num[], maxLag: number): LagCorr[] {
  const res: LagCorr[] = [];
  for (let lag = -maxLag; lag <= maxLag; lag++) {
    let a: Num[];
    let b: Num[];
    if (lag >= 0) {
      a = xs.slice(0, xs.length - lag);
      b = ys.slice(lag);
    } else {
      a = xs.slice(-lag);
      b = ys.slice(0, ys.length + lag);
    }
    res.push({ lag, corr: pearson(a, b) });
  }
  return res;
}

/** Approximate ±2/sqrt(n) white-noise significance band for a correlation. */
export function bartlettBand(n: number): number {
  return 2 / Math.sqrt(n);
}
