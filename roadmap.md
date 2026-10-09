# Roadmap: timing editor + Claude edits

Status: plan only, nothing built. Written 2026-10-09 against the V1.1 set; updated the same day for per-animation versioning (`animations/<Name>/vN.json`).

## Goal

Make **small edits to the existing animations** from inside the test bench:

- Retime them with sliders: phase lengths, individual keyframe times, overall speed.
- Change easing per segment with presets and a cubic-Bezier editor, the way Figma does it.
- Ask Claude for larger edits from a prompt box, then review the result next to the current version and accept or reject it.
- Save edits as a **draft** of that one animation, then promote the draft to its next version (`animations/<Name>/v(N+1).json` plus `.lottie`). Other animations are untouched.

## Non-goals

- Authoring from scratch: no new shapes or layers, and no drawing tools.
- Hosted editing. Editing works only through `serve.py` on 127.0.0.1. The hosted page stays read-only, and you publish with commit + push, as notes work today.
- Editing values (positions, colours, paths) with sliders. Use the Claude prompt for those.
- Spring easing (Figma's Gentle/Quick/Bouncy). Lottie keyframes support only cubic-Bezier easing, so a spring would have to be baked into many keyframes. Use Claude for that if it is ever needed.
- Build tooling. Keep the single `template.html`, stdlib Python and no npm.

---

## What the V1.1 JSON actually contains

Analysed all 8 files of the V1.1 set with python3. They now live as the latest `animations/<Name>/vN.json` of each animation. lottie-web 5.12.2 was then run headless in Chrome over every half-frame.

### Per animation

| Animation | op (frames) | sec | Layers | Animated props | Keyframes | Distinct key times¹ | Markers |
|---|---|---|---|---|---|---|---|
| Black White | 408 | 6.80 | 11 | 14 | 78 | 15 | 6 |
| Forgery | 389 | 6.48 | 12 | 18 | 185 (115 baked) | 16 | 4 |
| Glare | 210 | 3.50 | 7 | 8 | 94 (66 baked) | 8 | 4 |
| IncorrectId | 111 | 1.85 | 6 | 5 | 19 | 5 | 3 |
| Blur | 318 | 5.30 | 5 | 5 | 26 | 9 | 5 |
| CapturedFromScreen | 237 | 3.95 | 14 | 16 | 79 | 13 | 5 |
| PartialID | 180 | 3.00 | 4 | 6 | 32 | 12 | 4 |
| Obscure | 270 | 4.50 | 8 + 5 in precomp | 11 | 51 | 18 | 7 |
| **Total** | | | | **83** | **564** | | **38** |

¹ Distinct keyframe times, with baked tracks excluded.

### Global facts

- **Format:** every file is Bodymovin `v 5.9.0`, `fr` 60, `ip` 0, 2D (no `ddd`). Most canvases are 654×336. Blur is 654×328 and PartialID is 658×336.
- **Layer timing is trivial:** every layer has `st` 0 and `sr` 1, and almost every layer has `ip` 0 and `op` equal to the comp's `op`.
  - The exception is Obscure, where tick, card, hand, scene-card and bg-verified have `ip` 144. Their keyframes still start at t=0 or t=144.
  - So retiming whole layers via `ip/op/st` is an edge case here, not the main tool.
- **Only one precomp:** Obscure's `wrong` asset, used by layer `scene-wrong` (`ty 0`, `st 0`, plus a static rounded-rect mask). Precomp time equals comp time, so one retiming function can be applied inside it as well.
- **Features that are absent:** no expressions, no time remapping (`tm` on a layer), no trim paths, no mattes, no text, no 3D, no spatial Bezier (`ti`/`to`), no old-style `e` end values, and no fractional `t`.
- **One animated effect:** the Gaussian Blur `Blurriness` on Blur's `card` layer (`layers[].ef[0].ef[0].v`). Every other animated property is in `ks`: `o`, `s`, `p`, `r`. Forgery also animates one shape property (`highlight` `.shapes[0].it[0].s`, rect size).
- **Markers name the phases.** Examples: Blur has `idle, focus, sharp, verify, reset`. Obscure has `idle, reject, slide-out, hold-small, verify, hold-ok, loop-out`.
  - 55–84% of keyframes sit exactly on a marker boundary. The rest sit at stagger points inside a phase, such as 252 and 279 in Black White.
- **Keyframe times are shared across layers.** For example, CapturedFromScreen uses 75/99/225/237 on 7 layers. Even the largest file has only 18 distinct times. So the right primary control is a **time stop** that moves every keyframe at that time, not 564 separate diamonds.
- **1-frame cuts are deliberate.** Pairs such as 180/181 and 351/352 (Black White), 145/146 and 240/241 (Obscure) are instant swaps. Retiming must keep each pair exactly 1 frame apart.
- **Baked tracks:**
  - Forgery `badge` scale has 115 keyframes, one per frame from t=94 to t=207, with no easing.
  - Glare `glare` rotation and position have 33 keyframes each, every ~6.5 frames, all with easing (0.5,0.5,0.5,0.5), which is linear.
  - Show each one as a single block that can only be moved or stretched as a whole.
- **Last keyframe vs `op`:** usually the last key equals `op`. Some tracks end early: PartialID ends at 158 and 165 with `op` 180, and Obscure's `cross` ends at 210 with `op` 270.

### Easing

- **The arrays are per dimension, but always length 1.** Obscure has one exception, `slide` `p`, with `[0.55,0.55]`, and both values are equal. No file has different curves per dimension. So the UI edits one curve, writes it to every dimension, and expands the arrays to match.
- **Only 7 distinct curves are used.** They are listed as (o.x, o.y, i.x, i.y):

  | Curve | Uses | What it is |
  |---|---|---|
  | 0.4, 0, 0.4, 1 | 104 | house "ease-in-out" |
  | 0.5, 0.5, 0.5, 0.5 | 64 | linear (Glare's baked wobble) |
  | 0.3, 0, 0.16, 1 | 76 | house "ease-out" (expo-like) |
  | 0, 0, 1, 1 | 23 | linear |
  | 0, 0, 0.58, 1 | 17 | CSS `ease-out` (Glare) |
  | 0.5, 0, 0.5, 1 | 1 | ease-in-out |
  | 0.55, 0, 1, 1 | 1 | ease-in (Obscure slide) |

- **Hold keyframes** (`h:1`) are common. Forgery has 24, CapturedFromScreen 26 and Obscure 24, and Obscure's precomp `slide` has 5 out of 6 keyframes on hold.
- **Lottie stores a segment's easing on its first keyframe.** lottie-web reads segment k→k+1 as `getBezierEasing(kf[k].o.x, kf[k].o.y, kf[k].i.x, kf[k].i.y)`, so both handles come from `kf[k]`. The last keyframe's `i`/`o` are ignored.

### Bug found in the current files

**Glare and Forgery have non-hold keyframes with no `i`/`o`.** lottie-web then throws `Cannot read properties of undefined (reading 'x')` inside `renderFrame`. It reports this as a swallowed `renderFrameError`, so the frame renders incompletely and nothing shows in the console.

- **Glare:** keyframes at t=0 and t=144 on `tick`, `cross`, `glare` and `bg-verified` (`o`/`s`). In the headless sweep, errors appeared at frames 0.5–2.5.
- **Forgery:** the 115 baked `badge` scale keyframes have no easing at all. The sweep showed an error at frame 94.
- **Fix:** the editor's normaliser should add linear `i`/`o` to these keyframes. Alternatively, mark a keyframe `h:1` when its value equals the next keyframe's. This changes nothing visually and stops the throw.
- **Validation:** the validator should run the same frame sweep (see Validation below).

### dotLottie layout (confirmed from Glare's `.lottie`, now `animations/Glare/v2.lottie`)

- A `.lottie` file is a zip (deflate) that contains:
  - `manifest.json`: `{"version":"1","generator":"@dotlottie/dotlottie-js@1.8.0","author":…,"animations":[{"id":"<uuid4>","playMode":"normal"}]}`
  - `animations/<uuid4>.json`, byte-identical to the JSON in the JSON folder.
- There is no `images/` folder. `card` stays an external `card.png` (`e:0`, swapped at runtime), and `glare`, `vignette` and `qmark` are embedded base64 (`e:1`).
- The version zips contain one folder each: `IDCardRetake Animations - JSON/…` and `IDCardRetake Animations - dotLotiee/…`. Keep the `dotLotiee` spelling, because `build.py` depends on it.
- Python's `zipfile` and `uuid` modules can produce all of this.

---

## Data model: editable timing

### Extracting the timeline (pure function, client side)

```
timeline(data) -> {
  fr, op,
  markers: [{name, t0, t1}],              // from data.markers (tm, dr)
  stops:   [t...],                        // sorted distinct keyframe times of non-baked tracks, plus 0 and op
  lanes:   [{layerPath, layerName, ip, op,
             tracks: [{propPath, label, keys: [{t, h, ease:[x1,y1,x2,y2]|null}], baked: bool}]}]
}
```

- **Walk:** `layers[]`, plus `assets[].layers[]` for precomps, shown nested under the precomp layer. Collect every `{a:1, k:[…]}` found under `ks`, `ef` and `shapes`.
- **`propPath`:** a JSON Pointer to the `k` array, for example `/layers/3/ef/0/ef/0/v/k`. Writes go back through it.
- **`baked`:** set when a track has 30 or more keyframes and a median gap of 7 frames or less. Under that rule Forgery `badge.s` and Glare `glare.r`/`.p` are baked, and nothing else is.
- **Segment k:** runs from `keys[k]` to `keys[k+1]`, with easing from `keys[k].o`/`keys[k].i`, or `hold` when `keys[k].h`.

### One remap function does all the retiming

Every timing edit is expressed as a monotonic piecewise-linear map `f(t)` built from `(oldStop, newStop)` pairs, then applied everywhere at once.

| Edit | How `f` is built |
|---|---|
| Global speed ×s | `f(t) = t / s`. Easing handles are normalised, so they stay as they are. |
| Phase (marker) duration | Stretch `[t0, t1]` to its new length and shift every later stop by the difference. |
| Drag a time stop | Move one stop. Stops between it and its neighbours are clamped (see Pitfalls). |
| Drag one keyframe | Not a remap. Change `t` on that keyframe only, between its neighbours ±1. Phase 3. |
| Retime a whole layer | Shift that layer's keys plus its `ip`/`op`. Rarely needed, so it waits for phase 3 if it is ever wanted. |

Apply `f` to all of these:

- Every keyframe `t`, including baked tracks and the precomp's inner layers.
- `markers[].tm`, with `dr = f(tm+dr) - f(tm)`.
- Comp `op`.
- Every layer's `ip`/`op`, including precomp layers and the precomp layer's own `ip`/`op`.

Round the results to integer frames. They are all integers today, and lottie-web accepts fractions, but integers keep diffs clean.

### Pitfalls the code must handle

- **Monotonic `t`:** after a remap or drag, every track must still have strictly increasing `t`.
  - Clamp each stop to the space between its neighbours, `prev+1 … next-1`.
  - Treat stops 1 frame apart (180/181) as **locked pairs** that move together and stay 1 frame apart.
- **Hold keyframes:** move them with `f` like any other keyframe. Never add `i`/`o` to an `h:1` keyframe. When the user changes easing on a hold segment, delete `h` first.
- **Missing `i`/`o`:** run the normaliser described in the bug section on load, so every non-hold segment has easing.
- **Per-dimension easing arrays:** read `[0]` and write the same value to every index. Keep the array form when the source used arrays, which is every file here.
- **Last keyframe vs `op`:**
  - Shrinking the comp must not push keys past the new `op`. The remap handles this, because `f(op) = new op`.
  - A track that ends before `op` keeps its gap, scaled by `f`.
  - Never add or remove the final keyframe.
- **Layer `ip` vs keyframes:** Obscure layers start at `ip` 144 but some have a key at t=0. After a remap, keep `ip ≤` the first visible key, which holds automatically because `f` is monotonic. Never clip keys to `ip`.
- **Precomp time offset:** inner time = outer time − `st`, multiplied by `sr`. Here `st` = 0 and `sr` = 1, so `f` applies directly.
  - In general, use `f_inner(t) = f(t + st) - st`.
  - Refuse to edit a precomp whose `sr ≠ 1` or that has a layer with `tm`. None exist today.
- **Baked tracks:** a remap scales them proportionally, which is fine. They get no per-keyframe diamonds and no easing editor.

---

## Easing editor

### Mapping

- Segment k is `cubic-bezier(x1, y1, x2, y2)` with `x1 = kf[k].o.x[0]`, `y1 = kf[k].o.y[0]`, `x2 = kf[k].i.x[0]` and `y2 = kf[k].i.y[0]`. Writing a curve sets both handles on `kf[k]`, for every dimension.
- Clamp x to [0, 1]. y may go outside [0, 1] for overshoot ("back" curves).

### Presets

| Preset | cubic-bezier | Source |
|---|---|---|
| Linear | 0, 0, 1, 1 | – |
| Ease in | 0.42, 0, 1, 1 | Figma / CSS |
| Ease out | 0, 0, 0.58, 1 | Figma / CSS (already in Glare) |
| Ease in and out | 0.42, 0, 0.58, 1 | Figma / CSS |
| Ease in back | 0.3, -0.05, 0.7, -0.5 | Figma |
| Ease out back | 0.45, 1.45, 0.8, 1 | Figma |
| Ease in and out back | 0.7, -0.4, 0.4, 1.4 | Figma |
| House ease-in-out | 0.4, 0, 0.4, 1 | current files (104 uses) |
| House ease-out | 0.3, 0, 0.16, 1 | current files (76 uses) |
| Hold | `h:1` | Lottie step |

Confirm the Figma "back" values in Figma before shipping them.

### Curve editor

- A 200×200 inline SVG showing the unit square, the curve as `<path d="M0,1 C…">` with y flipped, and two draggable handle circles.
- Pointer events on the handles. Shift snaps to 0.05. Numeric inputs for x1, y1, x2 and y2 sit below.
- A small dot runs along the curve in time with playback so the result is easy to read.
- Preset chips sit above. If the current curve matches a preset within ±0.01, that chip is highlighted.
- **Multiple segments:** shift-click selects several segments, and applying a curve writes it to all of them. If the selection holds different curves, show "Mixed".

---

## UI sketch (inside the existing large view)

`openSheet` already rebuilds the player from `def.data` in `show(def)`. The editor holds a working copy and calls `show({...def, data: working})` after each change. The files are 4–22 KB, so a full `loadAnimation` reload costs nothing.

```
┌ sheet-head ─ Glare · v1.1 ─ [One card|All cards] ─ [Edit timing] ───────────────┐
│ ┌ view (existing preview) ───────────────────┐ ┌ Variations ───┐               │
│ │                                             │ │ Draft ●       │               │
│ └─────────────────────────────────────────────┘ │ v1.1  v1.0 …  │               │
│ transport: ▶ ■ ⟲  ──●────────── 129f / 210f                                     │
│ ┌ Timeline (only when Edit is on, only via serve.py) ────────────────────────┐ │
│ │ Phases  [glare 0–36][reject 36–99][clear 99–129][accept 129–210]  ← drag edges│ │
│ │ Stops    0 ┃ 36 ┃ 54 ┃ 99 ┃ 129 ┃ 144 ┃ 192 ┃ 210        ← drag ┃ = every key │ │
│ │ tick     o ◆────────────────◆──◆──────◆──◆                                  │ │
│ │          s ◆────────────────◆──◆                                            │ │
│ │ glare    r ▓▓▓▓▓▓▓▓▓▓▓▓▓ baked ▓▓▓▓▓▓▓▓▓▓▓                                   │ │
│ │ click a segment ─── → easing popover (presets + curve)                       │ │
│ │ Speed [ 1.00× ]  Duration 3.50s → 3.20s   ↶ ↷  Reset  Diff  Save draft       │ │
│ │ Ask Claude: [ make the reject phase snappier, ~0.3s shorter      ] [Send]    │ │
│ └──────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────┘
```

- **Lanes:** one row per animated property, grouped by layer. Layers with nothing animated are hidden. A precomp's layers are indented under it.
  - Lanes per animation: 5 to 18.
- **Diamonds:** ◆ marks an eased keyframe and ■ marks a hold.
- **Segments:** the line between two diamonds is the segment. Clicking it opens the easing popover. The line colour shows the preset in use.
- **Playhead:** a vertical line that follows the transport. Clicking the ruler seeks.
- **Live preview:** debounce for about 120 ms after a slider changes, rebuild, then `goToAndStop(currentFrame)` so the frame stays put while dragging.
- **Undo/redo:** a stack of JSON snapshots (`structuredClone`), capped at 100, bound to ⌘Z and ⇧⌘Z. Reset returns to the source version's data.
- **Diff vs original:** a list such as "reject: 63f → 45f", "tick.o @129: ease-out → house ease-out", "duration 3.50s → 3.20s". Compare the source and working timelines (same lanes, different `t` or ease), and add `build.py`'s `what()` summary.
- **Show draft vs source side by side** (later): reuse the "All cards" grid code with 2 cells and the existing synced `group()`.

---

## Claude prompt window

### Architecture

Browser → `POST /__claude` on `serve.py` (127.0.0.1) → subprocess → JSON back to the browser. Nothing runs on the hosted page.

**Recommendation: `claude -p` (headless Claude Code), not the API.**

| | `claude -p` | Anthropic API |
|---|---|---|
| Auth | Owner's existing login/subscription. No key handling. | `ANTHROPIC_API_KEY` in env, billed per token |
| Deps | None. `subprocess.run` | `urllib` is enough, but you write the request, retry and error code yourself |
| Structured output | `--json-schema` (present in installed v2.1.295) | Tool use / structured output |
| Lock-down | `--tools ""`, `--no-session-persistence`, `--system-prompt` | Inherently tool-less |
| Downside | Slower to start (a few seconds) and depends on the CLI being installed | Key management and cost |

Command, with the prompt passed on stdin:

```sh
claude -p --output-format json --json-schema "$SCHEMA" --tools "" \
       --no-session-persistence --system-prompt "$RULES" [--model <model>]
```

Read `result`/`structured_output` from the JSON envelope. Use a 120 s timeout. Allow one request at a time and return 409 while one is busy.

### Context sent

- **The animation JSON, trimmed:** replace every `assets[].p` that starts with `data:` with `"<embedded image>"`. Without the base64 every file is under 22 KB, so send the whole thing.
- **The timeline summary** from `timeline()`, as a compact text table:
  - markers and phases
  - lanes with keyframe times and easing preset names
  - which tracks are baked
- **The rules,** given as the system prompt:
  - do not touch `assets`
  - keep `fr` and `w`/`h`
  - keep `t` strictly increasing
  - easing goes on the segment's first keyframe
  - hold means `h:1` and no `i`/`o`
  - stay within 0 ≤ t ≤ op
  - answer only with the schema
- **Optionally the current draft:** if a draft exists, send it instead of the source, so requests build on each other.

### Response format: RFC 6902 JSON Patch (recommended)

Schema: `{summary: string, patch: [{op: "replace"|"add"|"remove"|"test", path, value?}]}`

Why a patch rather than full JSON:

- **The base64 images are never round-tripped.** The patch is applied to the original, untrimmed JSON.
- **The review is the patch itself:** "12 ops, all under `/layers/*/ks`", rather than a 20 KB blob to diff.
- **Edits outside the request are visible.** A path allow-list catches them, for example any change to `/assets/*` or `/fr`.
- **It is cheaper and faster** than having Claude echo back the whole file.

Apply the patch in the browser with a ~30-line function. Only `add`, `remove`, `replace` and `test` are needed.

### Validation before showing Accept

1. **Patch applies** and every path resolves. A failed `test` op rejects the result.
2. **Structural checks** (shared JS, with a Python copy used by promote):
   - the same asset ids, `w`, `h` and `p`
   - `fr` unchanged
   - layer count changed only if the prompt asked for it; otherwise warn
   - every track has strictly increasing `t`
   - every non-last, non-hold keyframe has `i`/`o`
   - handle x values within [0, 1]
   - all `t` within [0, op]
3. **lottie-web sweep:** load the result into a hidden 1×1 container, listen for `error`/`renderFrameError`, and call `goToAndStop(f, true)` for every frame up to `op`.
   - Any error rejects the result.
   - This is the same check that found the Glare and Forgery bug. It takes well under a second.

### Review flow

- The result appears as an **unsaved draft** in the large view.
  - It shows Claude's `summary`, the patch op list and the timeline diff.
  - An A/B toggle switches between Current and Proposed, both seeked to the same frame.
- **Accept** pushes the proposal onto the undo stack as the new working copy. Saving still needs "Save draft".
  - **Reject** discards it. **Refine** sends a follow-up prompt with the proposal as the base.
- **History:** each draft keeps `{prompt, summary, patch, at}` entries in a sidecar file, `animations/<Name>/draft.log.json`. This makes it possible to reconstruct how a draft was made and to write version notes.

---

## Saving model

Versioning is per animation, so a draft and its promotion only ever touch one animation's folder.

```
animations/<Name>/
  v1.json, v2.json, …        # released versions (+ vN.lottie)
  draft.json                 # working edit (full Lottie JSON), at most one per animation
  draft.log.json             # prompts / patches that produced it (optional)
```

### New `serve.py` endpoints (local only, same pattern as `/__notes`)

| Endpoint | Body | Effect |
|---|---|---|
| `POST /__draft` | `{name, data}` | Validate (Python checks), write `animations/<name>/draft.json`, rerun `build.py` |
| `POST /__draft` | `{name, data: null}` | Delete the draft, rebuild |
| `POST /__claude` | `{name, prompt, base}` | Run `claude -p` and return `{summary, patch}`. No file writes. |
| `POST /__promote` | `{name}` | Promote that animation's draft (below), rebuild |

Reject a `name` that contains `/` or `..`. Match it against existing animation folders.

### `build.py` changes

- If `animations/<Name>/draft.json` exists, put it at the top of that animation's `versions` as `{"v": "draft", …}`, with `what` computed against the latest release. It then shows in the large view's Versions panel with the existing detected-changes code.

### Promote: `POST /__promote {name}` (stdlib, ~30 lines in `serve.py`)

1. Rename `draft.json` to `v(N+1).json`, where N is the highest existing version.
2. Write `v(N+1).lottie`: a zip containing `manifest.json` (fresh `uuid4`, `playMode: "normal"`) and `animations/<uuid>.json` with identical bytes.
3. Move `draft.log.json` to `v(N+1).log.json`, or delete it. See the open questions.
4. Pre-fill `notes.json[name]["v(N+1)"]` from the draft log's summaries. Rebuild; `build.py` regenerates the "Latest" zips.

**Publishing:** `git add animations/<Name>/ notes.json index.html animations/latest-*.zip`, then commit and push. No change to that workflow.

---

## Phased plan

### Phase 1: retiming plus drafts (about 2 days)

What gets built:

- **Pure functions in `template.html`:** `timeline(data)`, `remap(data, f)`, `normalise(data)` (adds missing `i`/`o`) and `check(data)`, with structural checks and the lottie sweep. Add a `?test` mode that runs asserts on all bundled animations, matching the style of `serve.py test`.
- **The Timeline panel**, shown only when `EDIT` is true:
  - a phase bar (marker edges can be dragged)
  - a stops ruler (stops can be dragged, locked pairs move together)
  - lanes that are read-only in this phase
  - global speed, undo/redo, reset, and a duration readout
- **Draft saving:** `POST /__draft` and a `draft` entry in `build.py`, which then appears at the top of the Versions panel.

Done when:

- Opening every latest version with no edits and saving produces JSON equal to `normalise(original)`. The only difference is the added linear `i`/`o` in Glare and Forgery.
- Speed 2× halves `op`, every `t` and every marker, and the sweep passes.
- Shortening Glare's `reject` phase by 18f moves stops 54 and 99 back by 18 and leaves 0–36 unchanged.
- The Obscure 145/146 and 240/241 pairs stay 1 frame apart through every edit.
- The draft shows in the Versions panel with the right detected duration delta. The hosted build shows the same draft read-only, with no edit UI.

### Phase 2: Claude prompt plus promote (about 1.5 days)

What gets built:

- `POST /__claude` with `claude -p`, plus the trimming, schema and rules described above.
- A client-side patch applier, the A/B review, and accept/reject/refine.
- `draft.log.json`.
- `POST /__promote`.

Done when:

- "Make Blur's focus phase 0.5s shorter" returns a patch that passes validation and touches only `t`, markers and `op`.
- A patch that touches `/assets/0/p` is rejected with a clear message.
- Killing `claude` midway leaves no file changes.
- Promoting Glare's draft produces `animations/Glare/v3.json` and a `v3.lottie` that unzips to `manifest.json` plus `animations/<uuid>.json`, byte-equal to the JSON. The page shows Glare at v3, and every other animation is unchanged.

### Phase 3: easing and fine control (about 2 days)

What gets built:

- An easing popover per segment: presets, SVG curve editor, multi-select, and "Mixed".
- Per-keyframe dragging, clamped between neighbours.
- Hold toggle and layer `ip`/`op` handles.
- The diff list, and side-by-side Current/Draft playback.

Done when:

- Choosing "Ease out" on a segment writes `o:{x:[0],y:[0]}, i:{x:[0.58],y:[1]}` to `kf[k]`, for every dimension.
- A curve made from each preset round-trips: editor → JSON → editor gives the same numbers.
- Dragging a keyframe past its neighbour is blocked.
- Toggling hold on and off restores the previous curve.

Effort is for one engineer who knows the repo. Each phase can ship on its own.

---

## Open questions for the owner

1. **Should drafts be committed and visible on the hosted page** as a "draft" version, so others can review them? Or should `animations/*/draft*.json` be in `.gitignore` and stay local until promoted?
2. **Fix the Glare and Forgery missing-easing bug** as a new version of each (Glare v3, Forgery v4), or only as part of their next real edit? It also affects the shipped `.lottie` files used in the apps.
3. **Which Claude model and budget:** the default model, or pin one with `--model`? Is it fine that requests count against your Claude subscription usage?
4. **What should Claude be allowed to change?** Allow adding or removing layers and shapes, with a warning, or restrict it to timing, easing and existing values?
5. **Integer frames only,** or should sub-frame timing be allowed, for example for exact speed multipliers?
6. **Are the markers authoritative?** Should phase edits always keep markers in sync, and do the apps use these marker names for anything (such as segment playback)? If they do, the editor must never rename or drop them.

---

## Improvement notes

### Glare doesn't play correctly in the lottie-web viewer (owner to resolve)

- **Reported 2026-10-09:** Glare doesn't work in the web viewer.
- **Likely cause:** 9 keyframes in `animations/Glare/v2.json` are neither holds nor have `i`/`o` easing, starting with `/layers/0/ks/o` key 0 at t=0. On those frames lottie-web 5.12.2 throws `Cannot read properties of undefined (reading 'x')` and swallows it as `renderFrameError`, so the console shows nothing. The headless sweep found errors at frames 0.5–2.5.
- **Same problem elsewhere:** Forgery v3 has 116 such keyframes (first error at frame 94). The shipped `.lottie` files contain the same JSON.
- **Possible fixes:**
  - Re-export from the source tool with easing set on every keyframe.
  - Or add linear `i`/`o` (`{x:[1],y:[1]}` / `{x:[0],y:[0]}`) to the affected keyframes and save the result as Glare v3 and Forgery v4.
- **To check after fixing:** the Phase 1 frame sweep (`goToAndStop` on every frame, listening for `renderFrameError`) passes.
- **Still to confirm:** whether the glare streak and vignette (embedded webp assets) render as intended once the error is gone.

### Durations aren't uniform

- **Now:** durations range from 1.85s (IncorrectId) to 6.80s (Black White).
- **Wanted:** around 5.0–5.5s each. Shorten by trimming idle and hold time first. Lengthen by extending holds, not by slowing motion.

### Success states differ; IncorrectId's is the standard

- **Rule:** every animation with a correct/success state should match IncorrectId v2 exactly:
  - tick/checkmark and `bg-verified` fade in together over 24f (opacity ease 0.4/0.4)
  - scale 70→100 (ease 0.3/0.16)
  - then hold 45f
- **Today:** Black White (27f in, 54f hold), Blur (48f in), Forgery (29f in, scale starts 6f late), Glare (15f in, different curve), PartialID (overshoot 60→108→100, background not in sync) and Obscure (36f hold) all differ.

### Fixing all of these

`prompts/fix-animations.md` is a ready-to-send prompt for Claude Code. It covers durations, success states and missing easing in one pass. It writes new per-animation versions and never edits existing ones.

---

## Idea: end-to-end testing platform (not scheduled)

Merge this test bench with the owner's prototyping platform, the one used to come up with these animations. That platform is currently hosted on Railway. The goal is one place where people can view every animation and its versions, and preview it inside a mobile-sized view of the real flow, without any setup.

- **Waiting on:** the prototyping platform's source code from the owner.
- **Hosting move, Railway → Vercel:**
  - Vercel hosts the app but not the database itself.
  - The database would move to a free tier from a Vercel Marketplace provider (e.g. Neon or Supabase for Postgres), or stay on its current host.
  - Data transfer depends on the database type. For Postgres: `pg_dump` from Railway, then `pg_restore` / `psql` into the new database, then switch the connection-string env var in Vercel.
  - Check for anything Railway-specific: long-running servers or websockets, cron jobs, file storage on disk. These don't map directly to Vercel's serverless functions.
- **Integration options to evaluate once the code is in:**
  1. Embed this viewer as a route in the prototyping app.
  2. Embed the prototyping app's mobile view in the viewer's large view (a phone-frame preview).
  3. Share one data source (animations plus notes) that both read.
- **Mobile preview:** a phone-frame toggle in the large view (real device widths, safe areas, light/dark) is a cheap first step that doesn't depend on the merge.
