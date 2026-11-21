export const coordinatePlotStyles = `
.coordinate-plot {
  --chart-text: var(--profile-ink, var(--color-ink, #202020));
  --chart-muted: var(--profile-muted, var(--color-muted, #565656));
  --chart-grid: var(--profile-edge, var(--color-rule, #d7d7d7));
  --chart-surface: var(--profile-panel, var(--color-paper-2, #fafafa));
  --chart-accent: var(--profile-accent, var(--color-accent, #963d18));
  --chart-peer: var(--color-chart-bar, #7c8d9b);
  --chart-focus: var(--color-accent-2, var(--chart-accent));
  --chart-inset: clamp(2.85rem, 8vw, 4.4rem);
  color: var(--chart-text);
  font-size: .8125rem;
  font-variant-numeric: tabular-nums;
  isolation: isolate;
  margin-block: .75rem;
}
.coordinate-heading { display: flex; align-items: start; justify-content: space-between; gap: .4rem 1rem; flex-wrap: wrap; }
.coordinate-heading strong, .coordinate-x-title { font-weight: 650; }
.coordinate-heading label { display: inline-flex; align-items: center; gap: .35rem; color: var(--chart-muted); cursor: pointer; }
.coordinate-heading input { accent-color: var(--chart-accent); margin: 0; }
.coordinate-zoom { display: flex; flex-wrap: wrap; gap: .35rem; margin: .6rem 0; }
.coordinate-zoom button { min-height: 2.5rem; padding: .35rem .65rem; cursor: pointer; }
.coordinate-viewport { overflow-x: auto; overscroll-behavior-x: contain; }
.coordinate-canvas { min-width: 36rem; }
.coordinate-grid {
  position: relative;
  height: clamp(12rem, 30vw, 19rem);
  margin: 1.3rem 3rem 2rem var(--chart-inset);
  border-left: 1px solid var(--chart-grid);
  border-bottom: 1px solid var(--chart-grid);
  container-type: inline-size;
}
.coordinate-x-title { text-align: center; }
.coordinate-tick, .coordinate-guide { display: block; position: absolute; color: var(--chart-muted); pointer-events: none; }
.coordinate-tick-x { top: 0; bottom: 0; left: var(--at); border-left: 1px solid var(--chart-grid); }
.coordinate-tick-y { left: 0; right: 0; top: var(--at); border-top: 1px solid var(--chart-grid); }
.coordinate-tick span, .coordinate-guide span { position: absolute; white-space: nowrap; }
.coordinate-tick-x span { top: calc(100% + .37rem); translate: -50% 0; max-width: 5rem; overflow: hidden; text-overflow: ellipsis; }
.coordinate-tick-y span { right: calc(100% + .4rem); translate: 0 -50%; max-width: calc(var(--chart-inset) - .6rem); overflow: hidden; text-overflow: ellipsis; }
.coordinate-bar .coordinate-tick-x { border: 0; }
.coordinate-bar .coordinate-tick-x span { max-width: 5.4rem; overflow: hidden; text-overflow: ellipsis; }
.coordinate-guide { z-index: 1; color: var(--chart-text); font-weight: 650; }
.coordinate-guide-x { top: 0; bottom: 0; left: var(--at); border-left: 1px dashed var(--chart-focus); }
.coordinate-guide-y { left: 0; right: 0; top: var(--at); border-top: 1px dashed var(--chart-focus); }
.coordinate-target-area { position: absolute; left: 0; width: var(--area-width); height: var(--area-height); background: var(--color-chart-inset, #738e861e); pointer-events: none; }
.coordinate-mark { position: absolute; left: var(--column); top: var(--row); }
.coordinate-mark {
  display: grid; place-items: center; width: 1.35rem; height: 1.35rem; margin: 0; padding: 0; border: 0;
  border-radius: 50%; outline-offset: 1px; background: transparent; translate: -50% -50%; z-index: 2; color: inherit;
}
:is(a,button).coordinate-mark { cursor: pointer; }
.coordinate-mark::after {
  content: ""; width: .53rem; height: .53rem; border-radius: 50%;
  background: var(--chart-peer); border: 1px solid var(--chart-surface);
}
.coordinate-context .coordinate-mark::after { background: var(--chart-surface); border-color: var(--chart-muted); }
.coordinate-highlighted .coordinate-mark::after { background: var(--chart-accent); width: .65rem; height: .65rem; }
.coordinate-selected .coordinate-mark { z-index: 3; }
.coordinate-selected .coordinate-mark::after {
  background: var(--chart-accent); width: .71rem; height: .71rem; rotate: 45deg; border-radius: .11rem;
  outline: 1px solid var(--chart-accent); outline-offset: 3px;
}
.coordinate-mark:is(:hover,:focus-visible) { z-index: 6; outline: 2px solid var(--chart-focus); }
.coordinate-label-list { display: none; max-height: 12rem; overflow: auto; margin: .75rem 0 0; padding: 0 0 0 1.5rem; }
.coordinate-label-list li { margin-block: .25rem; overflow-wrap: anywhere; }
.coordinate-plot:has(input:checked) .coordinate-label-list { display: block; }
.coordinate-selection, .coordinate-guide-key { margin: .5rem 0 0; overflow-wrap: anywhere; }
svg.coordinate-line, .coordinate-bar-shape { position: absolute; pointer-events: none; }
svg.coordinate-line { inset: 0; width: 100%; height: 100%; }
.coordinate-line polyline { stroke: var(--chart-series, var(--chart-accent)); stroke-width: 2; vector-effect: non-scaling-stroke; fill: none; }
.coordinate-scatter .coordinate-line polyline { stroke-dasharray: 3 4; }
.coordinate-plot [data-series="0"] { --chart-series: var(--chart-accent); }
.coordinate-plot [data-series="1"] { --chart-series: var(--color-accent-2, #175a76); }
.coordinate-plot [data-series="2"] { --chart-series: var(--chart-muted); }
.coordinate-plot [data-series="3"] { --chart-series: var(--color-accent-3, #648754); }
.coordinate-line polyline[data-series="2"] { stroke-dasharray: 4 3; }
.coordinate-point[data-series]:not([data-series=""]) .coordinate-mark::after { background: var(--chart-series); }
.coordinate-bar-shape {
  left: var(--column); top: var(--bar-top); width: var(--bar-width); height: var(--bar-height);
  background: var(--chart-series, var(--chart-peer)); translate: -50% 0;
}
.coordinate-selected > .coordinate-bar-shape { background: var(--chart-accent); }
.coordinate-bar .coordinate-mark {
  left: var(--column); top: var(--bar-top); width: max(.65rem, var(--bar-width)); min-height: .9rem;
  height: var(--bar-height); border-radius: .12rem; translate: -50% 0; outline-offset: 2px;
}
.coordinate-bar .coordinate-mark::after { display: none; }
.coordinate-bar .coordinate-selected .coordinate-mark::after { display: block; position: absolute; top: -.35rem; }
.coordinate-popup {
  display: none; position: absolute; z-index: 7; pointer-events: auto; box-sizing: border-box;
  --popup-width: min(14.5rem, 100cqi);
  width: var(--popup-width); max-height: 9rem; overflow: auto; overflow-wrap: anywhere;
  top: clamp(0px, calc(var(--row) + .65rem), max(0px, 100% - 9rem)); left: clamp(0px, calc(var(--column) + .8rem), calc(100% - var(--popup-width)));
  padding: .55rem .65rem; border: 1px solid var(--chart-grid); border-radius: .35rem;
  background: var(--chart-surface); color: var(--chart-text); box-shadow: 0 5px 18px #0003; line-height: 1.3;
}

.coordinate-mark:is(:hover,:focus) ~ .coordinate-popup,
.coordinate-point:has(.coordinate-popup:hover) .coordinate-popup { display: block; }
.coordinate-grid:has(.coordinate-mark:focus-visible) .coordinate-mark:hover:not(:focus-visible) ~ .coordinate-popup { display: none; }
.coordinate-popup p { color: var(--chart-muted); margin: .22rem 0; }
.coordinate-popup dl { display: grid; gap: .3rem; margin: .4rem 0 0; }
.coordinate-popup dl > div { display: flex; justify-content: space-between; gap: .55rem; }
.coordinate-popup dt { color: var(--chart-muted); }
.coordinate-popup dd { margin: 0; font-weight: 650; text-align: right; }
.coordinate-empty { color: var(--chart-muted, inherit); }
@container (max-width: 24rem) {
  .coordinate-tick-x.coordinate-tick-minor:not(:last-child) span { display: none; }
  .coordinate-bar .coordinate-tick-x span { max-width: 3.75rem; }
}
`;
