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
