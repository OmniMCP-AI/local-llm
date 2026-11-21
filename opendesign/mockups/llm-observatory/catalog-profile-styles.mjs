import { coordinatePlotStyles } from "./coordinate-plot-styles.mjs";

export const profileStyles = `
.profile-document {
  margin: 0; background: #10100f; color: #f3eee5; color-scheme: dark;
  font: 16px/1.55 "Avenir Next", "Helvetica Neue", system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
}
.profile-shell {
  --profile-ink: #f3eee5; --profile-muted: #b8afa2; --profile-panel: #171715;
  --profile-edge: #39352f; --profile-accent: #ff9858;
  box-sizing: border-box; max-width: 72rem; margin: auto; padding: 0 clamp(1rem, 4vw, 2.75rem) 3rem;
}
.profile-shell * { box-sizing: border-box; }
.profile-shell a { color: var(--profile-accent); overflow-wrap: anywhere; }
.profile-shell a:hover { color: #ffbc91; }
.profile-shell :is(a,summary,input,button):focus-visible { outline: 2px solid #ffc299; outline-offset: 4px; }
.profile-nav, .profile-actions {
  display: flex; flex-wrap: wrap; align-items: center; gap: .5rem 1.2rem; font-size: .86rem;
}
.profile-nav { padding: 1rem 0; border-bottom: 1px solid var(--profile-edge); }
.profile-nav a { color: var(--profile-muted); text-decoration: none; min-height: 2rem; display: inline-flex; align-items: center; }
.profile-brand { display: inline-block; padding-top: 1rem; color: var(--profile-ink) !important; font-weight: 750; text-decoration: none; }
.profile-nav a[aria-current] { color: var(--profile-accent); }
.profile-actions a[aria-current] { color: var(--profile-ink); font-weight: 750; }
.profile-lookup { display: flex; align-items: center; flex-wrap: wrap; gap: .5rem; }
.profile-lookup label { flex-basis: 100%; }
.profile-lookup input { max-width: 100%; width: 22rem; }
.profile-lookup :is(input,button) { font: inherit; padding: .45rem .6rem; border: 1px solid #76716a; border-radius: .2rem; }
.profile-lookup button { cursor: pointer; }
.profile-hero { padding: clamp(1.25rem, 4vw, 3rem) 0; border-bottom: 1px solid var(--profile-edge); }
.profile-kicker { margin: 0 0 .55rem; color: var(--profile-accent); font: 650 .8rem/1.4 ui-monospace, monospace; }
.profile-shell h1 { margin: 0 0 .6rem; font-size: clamp(2rem, 6vw, 4.15rem); line-height: 1.04; letter-spacing: -.055em; overflow-wrap: anywhere; }
.profile-shell h2 { margin: 0 0 .65rem; font-size: clamp(1.3rem, 3vw, 1.7rem); letter-spacing: -.035em; line-height: 1.15; }
.profile-shell :is(h1,h2) { text-wrap: balance; }
.profile-shell p { text-wrap: pretty; }
.profile-hero .profile-evidence { margin: .4rem 0 .9rem; color: var(--profile-muted); }
.profile-actions a { display: inline-flex; min-height: 2.5rem; align-items: center; }
.profile-section { margin-top: 1.25rem; padding: clamp(1rem, 2.5vw, 1.6rem); border: 1px solid var(--profile-edge); background: var(--profile-panel); }
.profile-section p { color: var(--profile-muted); margin: .4rem 0 .7rem; }
.profile-fields { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 13rem), 1fr)); gap: .6rem 1.1rem; margin: .3rem 0 0; }
.profile-fields > div { padding: .6rem 0; border-top: 1px solid var(--profile-edge); min-width: 0; }
.profile-fields dt { color: var(--profile-muted); font-size: .83rem; }
.profile-fields dd { margin: .15rem 0 0; font-weight: 625; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.profile-specs { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 19rem), 1fr)); gap: .8rem; }
.profile-spec-graphic { margin: 1rem 0; color: var(--profile-muted); font-size: .8rem; }
.profile-spec-graphic meter { display: block; width: 100%; height: .75rem; margin-bottom: .4rem; }
.profile-spec-graphic meter::-webkit-meter-bar { background: var(--profile-edge); border: 0; border-radius: .25rem; }
.profile-spec-graphic meter::-webkit-meter-optimum-value { background: var(--profile-accent); border-radius: .25rem; }
.profile-spec-graphic meter::-moz-meter-bar { background: var(--profile-accent); border-radius: .25rem; }
.profile-gallery { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr)); gap: 1rem; margin-top: 1.25rem; }
.profile-gallery figure { margin: 0; }
.profile-gallery img { width: 100%; height: auto; max-height: 22rem; object-fit: contain; background: var(--profile-panel); outline: 1px solid #ffffff1a; }
.profile-gallery figcaption, .profile-video figcaption { color: var(--profile-muted); font-size: .84rem; }
.profile-video { margin: 1.25rem 0 0; max-width: 40rem; }
.profile-video img, .profile-video iframe { display: block; width: 100%; aspect-ratio: 16 / 9; border: 0; background: var(--profile-panel); }
.profile-video img { height: auto; aspect-ratio: 16 / 9; object-fit: cover; }
.profile-video summary { cursor: pointer; padding-block: .5rem; width: fit-content; }
.profile-photo-notices { color: var(--profile-muted); font-size: .84rem; margin-top: .75rem; }
.profile-photo-notices pre { white-space: pre-wrap; overflow-wrap: anywhere; }
.profile-footer { color: var(--profile-muted); margin-top: 1.2rem; overflow-wrap: anywhere; font-size: .85rem; }
.profile-chart-note { color: var(--profile-ink) !important; font-weight: 650; }
.profile-card-schematic { margin: 1.25rem 0; padding: .65rem 1rem; border: 1px solid var(--profile-edge); background: var(--profile-panel); }
.profile-card-schematic svg { display: block; width: min(100%, 34rem); margin-inline: auto; }
.profile-card-schematic figcaption { color: var(--profile-muted); text-align: center; font-size: .84rem; }
.profile-chart-table { width: 100%; margin-top: .65rem; text-align: start; border-collapse: collapse; font-size: .85rem; }
.profile-chart-table :is(th,td) { text-align: start; padding: .45rem; border-bottom: 1px solid var(--profile-edge); }
.profile-chart-table tr[aria-current] { background: #302016; }
.profile-directory-table { table-layout: fixed; overflow-wrap: anywhere; }
.profile-directory-table :is(th,td) { vertical-align: top; }
.profile-directory-table code { color: var(--profile-muted); font-weight: 400; }
@media (max-width: 520px) { .profile-shell { padding-inline: .9rem; } }
${coordinatePlotStyles}
`;
