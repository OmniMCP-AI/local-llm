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
.coordinate-grid {
  position: relative;
  height: clamp(12rem, 30vw, 19rem);
  margin: 1.3rem 1rem 2rem var(--chart-inset);
  border-left: 1px solid var(--chart-grid);
  border-bottom: 1px solid var(--chart-grid);
  container-type: inline-size;
}
.coordinate-x-title { text-align: center; }
.coordinate-tick, .coordinate-guide { display: block; position: absolute; color: var(--chart-muted); pointer-events: none; }
.coordinate-tick-x { top: 0; bottom: 0; left: var(--at); border-left: 1px solid var(--chart-grid); }
.coordinate-tick-y { left: 0; right: 0; top: var(--at); border-top: 1px solid var(--chart-grid); }
.coordinate-tick span, .coordinate-guide span { position: absolute; white-space: nowrap; }
.coordinate-tick-x span { top: calc(100% + .37rem); translate: -50% 0; }
.coordinate-tick-y span { right: calc(100% + .4rem); translate: 0 -50%; }
.coordinate-bar .coordinate-tick-x { border: 0; }
.coordinate-bar .coordinate-tick-x span { max-width: 5.4rem; overflow: hidden; text-overflow: ellipsis; }
.coordinate-guide { z-index: 1; color: var(--chart-text); font-weight: 650; }
.coordinate-guide span { background: var(--chart-surface); padding-inline: .17rem; }
.coordinate-guide-x { top: 0; bottom: 0; left: var(--at); border-left: 1px dashed var(--chart-focus); }
.coordinate-guide-x span { bottom: calc(100% + 1px); translate: -50% 0; }
.coordinate-guide-y { left: 0; right: 0; top: var(--at); border-top: 1px dashed var(--chart-focus); }
.coordinate-guide-y span { right: 0; bottom: 0; }
.coordinate-target-area { position: absolute; left: 0; width: var(--area-width); height: var(--area-height); background: var(--color-chart-inset, #738e861e); pointer-events: none; }
.coordinate-mark, .coordinate-label { position: absolute; left: var(--column); top: var(--row); }
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
.coordinate-label {
  display: none; z-index: 4; pointer-events: none; white-space: nowrap; translate: 0 calc(-100% - .55rem);
  transform: translateX(-50%); font-size: .75rem; line-height: 1; font-weight: 650;
  text-shadow: 1px 1px var(--chart-surface), -1px 1px var(--chart-surface), 1px -1px var(--chart-surface), -1px -1px var(--chart-surface);
  max-width: min(60%, 13rem); overflow: hidden; text-overflow: ellipsis;
}
.coordinate-plot:has(input:checked) .coordinate-label, .coordinate-selected .coordinate-label { display: block; }
.coordinate-selected .coordinate-label { color: var(--chart-accent); z-index: 5; }
.coordinate-line, .coordinate-bar { position: absolute; pointer-events: none; }
.coordinate-line { inset: 0; width: 100%; height: 100%; }
.coordinate-line polyline { stroke: var(--chart-accent); stroke-width: 2; vector-effect: non-scaling-stroke; fill: none; }
.coordinate-scatter .coordinate-line polyline { stroke-dasharray: 3 4; }
.coordinate-point > .coordinate-bar {
  left: var(--column, 0); top: var(--row, 100%); width: var(--bar-width); height: var(--bar-height);
  background: var(--chart-peer); translate: -50% 0;
}
.coordinate-selected > .coordinate-bar { background: var(--chart-accent); }
.coordinate-popup {
  display: none; position: absolute; z-index: 7; pointer-events: none; box-sizing: border-box;
  --popup-width: min(14.5rem, calc(100cqi + 1.5rem));
  width: var(--popup-width); top: var(--row); left: clamp(-.65rem, calc(var(--column) + .8rem), calc(100% - var(--popup-width) + .65rem));
  padding: .55rem .65rem; border: 1px solid var(--chart-grid); border-radius: .35rem;
  background: var(--chart-surface); color: var(--chart-text); box-shadow: 0 5px 18px #0003; line-height: 1.3;
}
.coordinate-mark:is(:hover,:focus) ~ .coordinate-popup { display: block; }
.coordinate-grid:has(.coordinate-mark:hover) .coordinate-mark:focus:not(:hover) ~ .coordinate-popup { display: none; }
.coordinate-popup p { color: var(--chart-muted); margin: .22rem 0; }
.coordinate-popup dl { display: grid; gap: .3rem; margin: .4rem 0 0; }
.coordinate-popup dl > div { display: flex; justify-content: space-between; gap: .55rem; }
.coordinate-popup dt { color: var(--chart-muted); }
.coordinate-popup dd { margin: 0; font-weight: 650; text-align: right; }
.coordinate-selection { display: block; margin-block: .45rem; color: var(--chart-accent); font-weight: 650; }
.coordinate-selection::before { content: "◆ "; }
.coordinate-empty { color: var(--chart-muted, inherit); }
@container (max-width: 24rem) {
  .coordinate-tick-x.coordinate-tick-minor:not(:last-child) span { display: none; }
  .coordinate-bar .coordinate-tick-x span { max-width: 3.75rem; }
}
`;
