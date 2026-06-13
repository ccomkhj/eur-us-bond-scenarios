import type { Num } from './stats';

export interface Panel {
  dates: string[];
  series: Record<string, Num[]>;
}

export interface Dataset {
  meta: { default_start: string };
  daily: Panel;
  monthly: Panel;
}

/** Slice a panel to rows whose date is >= start (ISO yyyy-mm-dd compares lexically). */
export function sliceFrom(panel: Panel, start: string): Panel {
  const from = panel.dates.findIndex((d) => d >= start);
  const i = from === -1 ? panel.dates.length : from;
  const series: Record<string, Num[]> = {};
  for (const [k, v] of Object.entries(panel.series)) {
    series[k] = v.slice(i);
  }
  return { dates: panel.dates.slice(i), series };
}

export async function loadDataset(url = '/data.json'): Promise<Dataset> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`failed to load ${url}: ${res.status}`);
  return (await res.json()) as Dataset;
}
