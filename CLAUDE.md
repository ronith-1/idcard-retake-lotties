# IDCard Retake Lotties — Test Bench

A single static page for previewing the ID-card retake Lottie animations (Blur, Glare, Forgery, PartialID, etc.) with a real or sample card image swapped in.

Live: https://ronith-1.github.io/idcard-retake-lotties/ (GitHub Pages from `main`, repo `ronith-1/idcard-retake-lotties`).

## Layout

- `template.html` — the page source. Edit this, not `index.html`.
- `build.py` — reads the animations and writes `index.html` by replacing the `/*__ANIMS__*/null` placeholder in the template with the data JSON.
- `index.html` — **generated**, committed because Pages serves it. Never hand-edit it.
- `previous.json` — the pre-v1.0 animation set, pulled out of the old `index.html`. Shown as the "Previous" version.
- `IDCARDS/*.png` — sample cards (Aadhaar, DL, PAN, Voter, generic). Every PNG here shows up in the "Sample cards" menu automatically.
- `IDCARDS/Animations/<folder>/` — one full set per release (`V1` = v1.0, `V1.1` = v1.0 + Obscure): `IDCardRetake Animations - JSON/*.json` (embedded into the page), the dotLottie folder, and a `.zip` of each (linked as downloads).
- `notes.json` — per version: `summary` and `why` (keyed by animation name). The "what changed" list is computed by `build.py` by comparing each version with the next-older one; only the "why" is written by hand.

## Build

```sh
python3 build.py   # stdlib only, no deps
```

Run it after any change to `template.html`, the V1 JSONs, `previous.json` or `IDCARDS/*.png`, then commit both `template.html` and `index.html`.

## Editing notes (local only)

```sh
python3 serve.py   # http://localhost:8765/ — Edit / Add buttons on Summary and Why
```

`serve.py` (stdlib, binds 127.0.0.1) serves the folder and adds `GET /__edit` (204 → the page shows edit controls) and `POST /__notes` (writes `notes.json`, reruns `build.py`). Static hosts (Vercel, Pages) 404 `/__edit`, so the hosted page is read-only. To publish edits: commit `notes.json` + `index.html`, push. `python3 serve.py test` runs its self-check. "What changed" is computed, not editable.

## How the page works

- `DATA = {versions:[{label, anims:[{name,data}], downloads?}], samples:[path]}` — inlined by `build.py`.
- Lottie-web 5.12.2 from cdnjs (`lottie.min.js`, SVG renderer).
- `withImage()` rewrites each animation's image assets (`assets[].p`) to a data URI. Only the `card` asset takes the chosen card, cover-cropped to the asset's `w×h` by `cover()`. With no image picked, a generated placeholder card is used (`placeholderCard` / `placeholderGlare`).
- Card image source: sample menu, or drop any image on the page. "Apply to all" re-renders every preview.
- Left: version list. Above the grid: "What changed in vX" accordion (closed by default; "Compared with vX →" jumps back a version). Changed cards get New / Updated badges.
- Large view (click a card): right panel lists the animation's variations across versions (matched by `key`); clicking one swaps the preview and shows its what-changed / why notes.
- Grid of previews per version; click one for the large sheet with play/pause, frame stepping (←/→), scrubber, `esc` to close.

## Adding a new animation version

1. Put the full set under `IDCARDS/Animations/<folder>/` (same structure as V1.1, both zips included).
2. Add `release("<label>", "<folder>")` at the top of `versions` in `build.py` (newest first).
3. Add `"<label>": {"summary": ..., "why": {name: reason}}` to `notes.json`.
4. `python3 build.py` (it prints the computed changes), commit, push. Pages redeploys on push.

Animations are matched across versions by name (`key()` in `build.py`: drops the `IDCard - ` prefix and ` vN` suffixes, maps `B&W` → `Black White`). A renamed animation will show as new unless `key()` maps it.

## Ignored

`.DS_Store`, `IDCARDS.zip`, `*.png.zip` (see `.gitignore`).
