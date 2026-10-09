# IDCard Retake Lotties — Test Bench

A single static page for previewing the ID-card retake Lottie animations (Blur, Glare, Forgery, PartialID, etc.) with a real or sample card image swapped in.

Live: https://ronith-1.github.io/idcard-retake-lotties/ (GitHub Pages from `main`, repo `ronith-1/idcard-retake-lotties`).

## Layout

- `template.html` — the page source. Edit this, not `index.html`.
- `build.py` — reads the animations and writes `index.html` by replacing the `/*__ANIMS__*/null` placeholder in the template with the data JSON. Also regenerates the two "Latest" zips.
- `index.html` — **generated**, committed because Pages serves it. Never hand-edit it.
- `animations/<Name>/vN.json` (+ optional `vN.lottie`) — **versioning is per animation**. Each animation has its own v1, v2, …; the highest is the one shown in the grid. The folder name is the display name.
- `animations/latest-json.zip`, `latest-dotlottie.zip` — **generated** by `build.py`: the latest version of every animation (fixed timestamps, so they only change when content does).
- `notes.json` — free-text changelog per animation version: `{"<Name>": {"v2": "...", ...}}`. Written by hand or via `serve.py`. `build.py` separately computes "Detected vs v(N-1)" and shows it read-only under each note.
- `IDCARDS/*.png` — sample cards, exported from Figma section 2347:11939 at 8× (SVG export → background stripped → headless Chrome render; transparent corners). Every PNG here shows up in the "Sample cards" menu and the All cards view. `GenericCardVertical.png` has no Figma source and is still low-res.
- `IDCARDS/default.png` (or .jpg/.webp) — the production generic card (Figma GenericCard). It's the default image for every animation and the reset target; without it the generated placeholder is used.
- `errors.json` — drawer title per animation for the Preview tab (`{"_default": {title}, "<Name>": {title}}`), taken from the Figma "Action sheet" frames.
- `preview/assets/` — status bar, notch, spinner, icons and the sample captured photo, exported from Figma (file `AhabHjUgLUZpzTduxarUEA`, screens 1123:14315 processing / 1123:14385 error / 1123:14440 drawer).
- `prompts/fix-animations.md` — ready-to-send Claude Code prompt to unify durations / success states and fix missing easing (writes new per-animation versions).
- `roadmap.md` — improvement notes, the planned timing editor (keyframe sliders, Bezier easing) and Claude prompt window. Not built yet.

History: before per-animation versioning there were whole-set folders (`IDCARDS/Animations/V1`, `V1.1`) and `previous.json`; they were split into `animations/` (Previous → v1, plus Forgery v2 from "Forgery v2"; v1.0 → next; v1.1 only added Obscure). See git history before that change.

## Build

```sh
python3 build.py   # stdlib only, no deps
```

Run it after any change to `template.html`, `animations/`, `notes.json` or `IDCARDS/`, then commit `index.html` and `animations/latest-*.zip` along with the sources.

## Adding a new version of an animation

1. Save it as the next number: `animations/Glare/v3.json` (and `v3.lottie` if you have it).
2. Add a note: `"Glare": {"v3": "..."}` in `notes.json`, or type it in the page via `serve.py`.
3. `python3 build.py`, commit, push. Pages redeploys on push.

A brand-new animation is a new folder with `v1.json`.

## Editing notes (local only)

```sh
python3 serve.py   # http://localhost:8765/ — notes become editable textareas
```

`serve.py` (stdlib, binds 127.0.0.1) serves the folder and adds `GET /__edit` (204 → notes become textareas) and `POST /__notes` (`{name, version, note}`; writes `notes.json`, reruns `build.py`). Fields save on blur or ⌘/Ctrl+Enter. Static hosts (Vercel, Pages) 404 `/__edit`, so the hosted page is read-only. To publish edits: commit `notes.json` + `index.html`, push. `python3 serve.py test` runs its self-check. Restart `serve.py` after editing it.

## How the page works

- `DATA = {anims:[{name, versions:[{v, data, json, lottie, note, what}]}] (newest first), downloads, default, samples}` — inlined by `build.py`. On load each version gets `.name` and `.anim` (back-reference) so it can be used as a card `def`.
- Lottie-web 5.12.2 from cdnjs (`lottie.min.js`, SVG renderer).
- `withImage(def, img)` rewrites each animation's image assets (`assets[].p`) to a data URI. Only the `card` asset takes the chosen card, cover-cropped to the asset's `w×h` by `cover()` but rasterised at the source's resolution (up to 4×) so it stays sharp when scaled up; the cache key includes the image src. Without a card, `placeholderCard` / `placeholderGlare` are drawn.
- Card image source: sample menu, or drop any image on the page. "Apply to all" re-renders every preview.
- Grid: latest version of each animation, with a version pill. Header has the "Latest" zip downloads.
- Top bar: "Animations | Preview" tabs (`setTab()`, `#preview` in the URL). The card picker is shared by both.
- Large view (click a card): full-window toggle (button or `f`, remembered); "One card | All cards". All cards = the animation once per sample card, kept in sync by `group()` so the transport and keys drive them all. Right panel: the animation's versions, newest first; picking one swaps the preview and shows its changelog note, detected changes vs the previous version, and per-version JSON / dotLottie downloads.
- Preview tab: a 375×812 phone (`.pv`, 1:1 CSS px, scaled to fit with a transform) built from the Figma screens — status bar, notch, home indicator included. Animation + Version pickers, **Play** runs the Figma prototype timing (processing 800ms → 300ms dissolve to error → 750ms → 800ms ease-in-back slide of the drawer, scrim rides with it) and starts the Lottie (`xMidYMid slice` in a 325×166 box) only after the slide. Processing / Error / Drawer jump buttons show a state statically. Switching animation/version on the drawer swaps the Lottie in place. The grid pauses while Preview is showing. Fonts: Inter 3.19 from jsdelivr (closer to Figma than Google's Inter 4).
- `?shot=processing|error|drawer&anim=<Name>&v=<index>&frame=<n>` renders one screen unscaled at (0,0) with no transitions, for pixel diffs against Figma exports (headless Chrome `--window-size=375,812`). Last verified: all 3 screens < 0.6% px differing at 1× and < 0.3% at 2× (threshold 16/255; Lottie box masked on the drawer); the remainder is glyph-edge anti-aliasing.
- Transport: play/pause, stop, loop, scrubber; in the large view `space`, `←`/`→` frame step, `esc` close.

## Known issue

The latest Glare (v2) and Forgery (v3) have non-hold keyframes with no `i`/`o` easing. lottie-web swallows the resulting error (`renderFrameError`) on those frames. See `roadmap.md` and its open questions.

## Ignored

`.DS_Store`, `IDCARDS.zip`, `*.png.zip` (see `.gitignore`).
