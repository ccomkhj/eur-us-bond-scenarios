import { loadDataset, sliceFrom, type Dataset } from './data';
import { renderOverlay, renderLeadLag, renderRollingCorr, type Mode } from './charts';

const $ = <T extends HTMLElement>(id: string): T => {
  const el = document.getElementById(id);
  if (!el) throw new Error(`missing #${id}`);
  return el as T;
};

function rerender(data: Dataset): void {
  const start = ($('start') as HTMLInputElement).value || data.meta.default_start;
  const window = Number(($('window') as HTMLInputElement).value);
  const maxLag = Number(($('maxlag') as HTMLInputElement).value);
  const mode = (($('mode') as HTMLSelectElement).value as Mode);

  $('windowVal').textContent = String(window);
  $('maxlagVal').textContent = String(maxLag);
  $('warn').textContent =
    mode === 'levels'
      ? 'Levels are non-stationary — correlation on levels is often spurious. Compare against "changes".'
      : '';

  const panel = sliceFrom(data.daily, start);
  renderOverlay($('overlay'), panel);
  renderLeadLag($('leadlag'), panel, maxLag, mode);
  renderRollingCorr($('rollcorr'), panel, window, mode);
}

async function boot(): Promise<void> {
  const data = await loadDataset();
  ($('start') as HTMLInputElement).value = data.meta.default_start;
  for (const id of ['mode', 'start', 'window', 'maxlag']) {
    $(id).addEventListener('input', () => rerender(data));
  }
  rerender(data);
}

void boot();
