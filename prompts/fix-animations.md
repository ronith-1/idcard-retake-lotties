# Prompt: fix and unify the ID-card retake Lotties

Paste everything below the line into a Claude Code session opened in this repo (`TestingBench-Lotties`), and let it run. It needs to write files and run Python, so approve those when asked, or start the session in auto mode.

Two choices are marked **[CHOICE]**. Edit them before sending if the defaults are wrong.

---

You are fixing the ID-card retake Lottie animations in this repo. Read `CLAUDE.md` first: it explains the layout and the build. Each animation lives in `animations/<Name>/vN.json` (plus `vN.lottie`). Versioning is per animation, so **never edit an existing `vN` file**. For every animation you change, write the next version (`v(N+1).json` and `v(N+1).lottie`) next to it.

## Animations (latest versions, all 60fps, ip 0)

| Animation | Latest | Duration | Success layers | Success fade-in | Hold | Exit |
|---|---|---|---|---|---|---|
| Black White | v2 | 6.80s (408f) | tick, bg-verified | 27f (252→279), scale from 252 | 54f | 18f fade |
| Blur | v2 | 5.30s (318f) | checkmark, bg-verified | 48f (204→252) | 48f | 18f fade |
| CapturedFromScreen | v2 | 3.95s (237f) | tick, bg-verified | 24f (144→168) | 45f | 12f fade |
| Forgery | v3 | 6.48s (389f) | tick, bg-verified | 29f (311→340), scale starts 317 | 37f | 12f fade (opacity only) |
| Glare | v2 | 3.50s (210f) | tick, bg-verified | 15f (129→144), easing (0,·,0.58,·), missing handles | 48f | 18f fade |
| IncorrectId | v2 | 1.85s (111f) | tick, bg-verified | **24f (42→66): the reference** | 45f | none (ends on 100) |
| Obscure | v1 | 4.50s (270f) | tick, bg-verified (layer ip 144) | 24f (186→210) | 36f | 24f fade |
| PartialID | v2 | 3.00s (180f) | checkmark, bg-verified | checkmark 45f with overshoot 60→108→100; bg 60f (39→99), not in sync | 45f | 23f / 30f, not in sync |

Markers (`markers[].cm/tm/dr`) name each phase. Keep them, and move them with any retiming.

## Task 1: one success state for every animation, copied from IncorrectId

Every animation ends in a success state: a tick or checkmark layer plus `bg-verified`. Make all of them identical to IncorrectId v2's. These are its exact keyframes (frame times relative to the start of the success entrance, which is t=42 in IncorrectId):

```
tick / checkmark  opacity: 0 (hold) → at +0: 0, o{x:[0.4],y:[0]} i{x:[0.4],y:[1]} → at +24: 100
tick / checkmark  scale:   [70,70] (hold) → at +0: [70,70], o{x:[0.3],y:[0]} i{x:[0.16],y:[1]} → at +24: [100,100]
bg-verified       opacity: 0 (hold) → at +0: 0, o{x:[0.4],y:[0]} i{x:[0.4],y:[1]} → at +24: 100
```

- **Entrance:** tick/checkmark opacity and scale, plus bg-verified opacity, all start on the same frame and last exactly 24f with those curves. No overshoot (fix PartialID's 60→108→100) and no offset start (fix Forgery's scale starting 6f late).
- **Hold:** exactly 45f at full opacity.
- **[CHOICE] Exit:** IncorrectId has no exit because it's short. Use the same 12f fade-out to 0 on tick/checkmark and bg-verified, with o{x:[0.4],y:[0]} i{x:[0.4],y:[1]}, then end the animation. *(Alternative: no fade, end on the success frame like IncorrectId.)*
- **Visual design:** if the tick/checkmark shape itself, its position, the bg-verified colour/size, or the layer names differ from IncorrectId, report the differences in your summary. Change them to match only if the difference is clearly unintentional (e.g. a different green). Don't redraw shapes.

## Task 2: uniform duration

- **[CHOICE] Target:** every animation is **5.0–5.5s (300–330f)**. *(Alternative: only cap the long ones at 5.5s and leave shorter ones as they are.)*
- **To shorten** (Black White 6.80s, Forgery 6.48s): trim idle and hold phases first; only then speed up motion phases.
- **To lengthen** (IncorrectId, PartialID, Glare, CapturedFromScreen, Obscure): extend the idle/hold phases before the failure moment and between phases. Don't slow the motion itself. Fast moves should stay fast.
- **Keep the success block** from task 1 (24f entrance + 45f hold + exit) unchanged at the end of each animation.
- **Retiming rules:**
  - Shift every keyframe `t`, layer `ip`/`op`/`st` and marker `tm`/`dr` consistently, including inside precomps (Obscure has one).
  - Keep keyframe times strictly increasing per property.
  - Keep deliberate 1-frame cuts 1 frame apart (e.g. Obscure 145/146 and 240/241; check others).
  - Set root `op` to the new end.
- **Many keyframes:** some properties have a keyframe every few frames (Forgery's badge has ~115). Treat those as one block and scale the block; don't move its keyframes one by one.

## Task 3: missing easing (a real rendering bug)

- **The bug:** non-hold keyframes need both `o` and `i` handles, except the last keyframe of a property. Glare v2 has 9 keyframes without them (e.g. `/layers/0/ks/o` key 0) and Forgery v3 has 116 (first at `/layers/4/ks/s` key 0, t=94). lottie-web 5.12.2 throws `Cannot read properties of undefined (reading 'x')` on those frames and swallows it as `renderFrameError`, so nothing appears in the console. Glare doesn't play correctly in the web viewer.
- **Fix:** add easing to every such keyframe. Use linear (`o{x:[0],y:[0]} i{x:[1],y:[1]}`, one array entry per dimension) unless the motion obviously needs the curve used on neighbouring keyframes of the same property.
- **Scope:** check all 8 animations, not just these two.

## Constraints

- Don't touch image assets: no changes to `assets[].p` / `w` / `h`. The `card` asset is swapped at runtime and the embedded webp/png data URIs must stay byte-identical.
- No new layers, shapes or expressions. Don't change colours, paths or positions except as allowed in task 1.
- Keep 60fps, canvas sizes and layer names.

## Outputs

1. **New JSON:** `animations/<Name>/v(N+1).json` for every animation you change, written compact (`separators=(",",":")`).
2. **New dotLottie:** `animations/<Name>/v(N+1).lottie`. It's a zip containing:
   - `manifest.json`: `{"version":"1","generator":"@dotlottie/dotlottie-js@1.8.0","author":"@dotlottie/dotlottie-js@1.8.0","animations":[{"id":"<uuid4>","playMode":"normal"}]}`
   - `animations/<uuid4>.json`: byte-identical to the `.json`. Use Python's `zipfile`.
3. **Notes:** add an entry per new version to `notes.json` (`{"<Name>": {"v(N+1)": "..."}}`). In plain language, say what changed: new duration, success state unified, easing fixed.
4. **Build:** run `python3 build.py`.
5. **Verify with a script and report the results:**
   - JSON parses.
   - Every non-hold, non-last keyframe has `i` and `o`.
   - Times are monotonic.
   - Durations are within the target.
   - Success block timings match IncorrectId's frame for frame (relative).
   - Assets are byte-identical to the previous version.
   - Each `.lottie` unzips to JSON equal to the `.json`.
   - **If Chrome/Playwright is available:** load each new version in lottie-web 5.12.2, call `goToAndStop(f, true)` for every frame, and confirm no `renderFrameError` fires.
6. **Summary table:** a short table per animation with old → new duration, what you trimmed or extended, success-state fixes, easing fixes, and anything you weren't sure about.

Don't commit. Leave the changes for review in the test bench (`python3 serve.py`, then open each animation and compare versions).
