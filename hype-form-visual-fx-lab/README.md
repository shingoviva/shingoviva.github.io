# HYPE FORM / Visual FX Lab v28.2.34

Production Tool / Core Stability Audit + Smooth Preview Runtime + Portable Project Restore + Source-First FX + Export Regression Lock


## v28.2.34

### Full core-stability / recent-regression audit

This release is intentionally a **bug-fix and production-hardening pass**, not a feature release. The v28.2.31 smooth playback path, v28.2.32 source-signal simulation and v28.2.33 fixed Viewer geometry remain the baseline.

- **Export mutation guard strengthened without changing the protected Export renderer.** `exportProjectSignature()` now covers Master Intensity / Motion / Type, source generation, Subject/Depth analysis generation, subject background mode and AI-ready state, in addition to the existing Timeline / typography / Final Look / clip controls. A render-critical change during offline export can no longer evade the invariant check. The 13 hash-locked Export functions remain unchanged.
- **Project OPEN now validates before source replacement.** Schema, Timeline graph, duplicate IDs, referenced FX and the saved metadata fingerprint are checked before the current source is mutated.
- **Portable local fonts.** If the active font was imported from the local-font picker, its bytes are bundled in `.hypeproj` and reinstalled before typography state is restored. A missing required font is reported instead of silently substituting another font.
- **AI analysis integrity.** Bundled Subject Mask / Depth Map assets now carry lightweight content fingerprints and are verified after restoration.
- **Project save asset snapshot.** Source file, selected local font and AI analysis canvases are snapshotted before asynchronous ZIP generation, preventing a source/AI update from mixing two moments into one bundle.
- **Project session boundary fixed.** Successful Project OPEN clears Undo/Redo. Cross-project Undo is intentionally not offered because it cannot safely restore prior source-media bytes. Restored `nextLayerId` is normalized above every existing Timeline ID.
- **Project/source operations are locked during export.** SAVE, OPEN and source replacement cannot mutate the render graph while an offline export is active.
- **Live AI scheduling hardened.** The scheduler is source-version guarded, re-checks frame-budget conditions immediately before inference and no longer uses a forced `requestIdleCallback` timeout that could fire under load.
- **Slow Shutter avoids unnecessary Optical Flow.** `Slow Shutter / Frame Accumulation` uses its real temporal history only; Motion Flow is requested only by the Natural / Long Tail drag-shutter styles.
- **GPU fallback hardened.** Failed shader compilations are cached so the same unsupported shader is not compiled/fails every frame. WebGL context loss explicitly falls back to Canvas and resets GPU resources on context restoration.
- **Paused video cache fix.** Changing the project background while a contained video is paused refreshes the cached composite, preventing stale letterbox color.
- **Retryable dynamic script loader.** Failed external script nodes are removed so a later retry can succeed; an existing in-flight script is awaited rather than assumed loaded.
- Added `CORE_STABILITY_AUDIT.md` / `verify_core_stability.py` plus `verify_release.py` to run all release contracts in one command. Updated Preview and Project contracts for the hardened scheduler and portable-font / AI-asset restore behavior.
- Project schema intentionally remains **313** for v28.2.33 compatibility.

### QA in this release

- `node --check` on the application script
- Export Contract: protected 13-function hash baseline unchanged
- Project Save / Restore Contract
- Preview Stability Contract
- Viewer Layout Contract
- Final Look Contract
- Source-First FX Contract
- Core Stability Audit
- Actual Chromium smoke pass through all non-Original FX using an injected local document harness; no application exceptions were observed. Network-only AI model fetches are expected to fail in the restricted smoke environment.

## v28.2.33

### Fixed Viewer geometry / no proxy-layout jitter

- Decoupled **Viewer display size** from internal Preview proxy canvas `W/H`. Auto Preview may change render resolution for performance, but the on-screen Viewer box no longer changes size.
- `fitViewerStage()` now derives aspect only from the project/source aspect contract (`activeProjectRatio()`), not the rounded internal proxy dimensions.
- `resizeProjectCanvases()` is now render-buffer-only and never writes Viewer CSS geometry.
- Viewer geometry changes only for real layout events: window/panel resize, Focus Preview, or project/source aspect change.
- Removed width/height animation from `.viewer-stage`; heavy rendering cannot make the editing UI visually pulse or wobble.
- Added cached integer Viewer dimensions and coalesced `ResizeObserver` updates so repeated layout notifications cannot create feedback-loop resizing.
- Added Viewer geometry diagnostics to `previewStats()` and a new `VIEWER_LAYOUT_CONTRACT.md` / verifier.
- v28.2.31 playback synchronization and v28.2.32 signal simulation remain unchanged. Export protected functions remain unchanged.


## v28.2.32

### Analog / physical FX source-signal pass

- Rebuilt **Analog Signal → Signal Dropout** as signal-domain damage instead of painted white streaks. The incoming scanline is sampled for local luma-detail and chroma energy; a deterministic defect field damages Y/C content, uses neighboring previous-scanline compensation, attenuates chroma, and adds residual RF-like signal noise.
- Removed the extra painted CRT/NTSC black scanline bars and VHS/bad-tracking white bottom bands from `Analog Signal`. Scanline visibility is now multiplicative modulation of source pixels; lower-raster damage is source-line replacement / timebase shift / chroma loss.
- Rebuilt **Tape Deck → Tape Dropout / Tape Crease / Head Switch** so damage occurs inside the source luma/chroma signal path. Dropout uses scanline compensation instead of white wash segments; crease alters sampling/bandwidth/chroma; head switching substitutes and shifts source signal near the lower raster instead of drawing white lines.
- Moved Tape Deck generation-loss black lift into the signal transform itself instead of applying a full-frame screen-color wash.
- Replaced the **Shockwave** CPU fallback. If WebGL is unavailable it now radially remaps source pixels around the wavefront; the old white-circle fallback is gone.
- Replaced the **Advanced Bloom** CPU fallback with source-highlight extraction + blur. It no longer blooms the whole frame indiscriminately when the GPU path is unavailable.
- Expanded the Source-First regression verifier from 8 to **12 audited FX** and added `SIGNAL_SIMULATION_CONTRACT.md`.
- Physical defect geometry remains deterministic for a fixed project time. Source content controls how strongly the damaged signal is visible; the simulation does not simply schedule decorative overlays.
- Line-energy analysis is intentionally sparse-sampled to avoid unnecessary playback cost.
- Export protected functions are unchanged. Preview timing / decoder synchronization from v28.2.31 is untouched.

### Audit result

The optical / analog / motion categories were scanned again for full-frame fills, gradients, geometric strokes and time-driven shapes. Remaining uses in Source-First FX are either masks/tints derived from real source highlights/edges/motion, or intentional design/compositing effects. The concrete legacy physical-simulation substitutions found in this pass were Analog Signal, Tape Deck, Shockwave fallback, and Advanced Bloom fallback; those are now corrected.

## v28.2.31

### Preview playback timing / decoder sync fix

- Reverted the v28.2.30 decoded-frame-counter reuse path. `getVideoPlaybackQuality().totalVideoFrames` is no longer used as a gate for Viewer cache updates; on some browsers that counter can advance in bursts and make motion look like periodic freezes.
- Added a `requestVideoFrameCallback()` frame pump. The Viewer cache is refreshed when the browser actually presents a decoded video frame, rather than polling/copying the `<video>` element from every render RAF.
- Normal forward playback no longer hard-seeks whenever source/timeline drift exceeds ~140 ms. Hard seeks are now reserved for actual discontinuities: play/scrub sync, project loop wrap, or selected IN/OUT source-loop wrap. Small drift is corrected gradually through `playbackRate`.
- Removed the unstable 45 fps governor tier. Viewer pacing is now 60 fps / 30 fps only, with sustained-load hysteresis. A no-FX/lightweight project is pinned to 60 fps.
- Fixed the 60 Hz scheduling boundary: a nominal 16.7 ms threshold could miss a ~16.67 ms RAF and create an accidental 33 ms gap. Viewer rendering now uses RAF-tolerant timing.
- Auto Preview canvas resizing remains deferred outside active playback; Live AI scheduling and lazy feedback buffers from v28.2.30 remain.
- Added preview sync diagnostics: hard-seek count, soft-sync count, maximum sync error, current/presented media time, and frame-pump state.
- Export pipeline protected functions are unchanged and still verified separately.

### Browser smoke test

A 6 s / 30 fps H.264 test clip was loaded in actual headless Chromium with a 5 s project and **zero FX layers**. The Viewer was allowed to run for 12 s (more than two Timeline loops). Results: Viewer tier remained 60 fps, render-cost EMA settled below ~1.6 ms, no long render frames were recorded, the presented-frame pump stayed active, and hard seeks occurred only at explicit playback/loop synchronization boundaries — not repeatedly inside each 5 s pass.

## v28.2.30

### Preview smoothness / memory-bandwidth pass

- Investigated the repeatable playback hitch reported around ~1.4 s. The code contained a concrete ~1.5 s trigger: **Live Depth** could launch a new Depth Anything inference directly from the render hot path whenever `depthLastUpdate > 1500 ms`. This is now removed from the hot path.
- Live Depth / Live Matte refreshes are now **deferred and playback-budget gated**. Depth refresh is heavily throttled and only scheduled when the Viewer is maintaining timing headroom; the last valid depth/matte remains usable between refreshes.
- Timeline layer feedback canvases are now **lazy**. Previously every FX layer allocated and recopied a full-resolution previous-frame canvas every rendered frame, even if that FX never used temporal feedback. Only Tape Deck, Block Mosh, Datamosh Pro, Paparazzi Flash, Optical Flow Bloom, Speed Ramp and Flow Trails now own/update that buffer.
- **Auto Preview no longer resizes the entire canvas graph during playback.** It may decide that the next playback should use a different proxy size, but the expensive canvas rebuild is deferred to pause / the next playback boundary.
- Video preview caching now checks the browser decoded-frame counter (`getVideoPlaybackQuality().totalVideoFrames`) and avoids recopies when no new decoded video frame exists.
- Added Viewer diagnostics (`previewStats`) for frame-time EMA, maximum render cost, long-frame count, FPS tier, active feedback/history canvas counts and pending Auto Preview resolution.
- Added `PREVIEW_STABILITY_CONTRACT.md` and `verify_preview_stability.py`.
- Export rendering is unchanged. The 13 protected Export Contract functions still pass byte-level hash verification.

### Why this is not treated as only a RAM problem

The periodic hitch was a combination of **GPU/CPU contention and memory bandwidth**, not simply running out of memory. Full-frame Canvas copies, canvas reallocations and AI inference can each create a visible main-thread / GPU synchronization pause even when total RAM usage is still safe. v28.2.30 removes or defers those operations from the playback hot path.

## v28.2.29

- Added a collapsible **FINAL LOOK / MASTER OPTICS** panel directly under the Live Viewer.
- Final-composite controls: **Exposure (EV), Contrast, Highlights, Shadows, Saturation, Temperature, Tint**.
- Exposure is processed in linear-light space through the GPU Final Look shader rather than a CSS brightness overlay. A deterministic CPU fallback is kept for systems where WebGL fails.
- Final Look is applied once after Timeline FX + Typography + Strobe. Master feedback stores the pre-grade composite so color/exposure adjustments cannot accumulate from frame to frame.
- Final Look state is included in portable `.hypeproj` save/restore, undo/redo snapshots, and the export mutation signature.
- Added `FINAL_LOOK_CONTRACT.md` and `verify_final_look.py`.
- Export pipeline protected functions remain unchanged.

## v28.2.28

### Portable project save / exact restore

Project SAVE was rebuilt as a real work-session snapshot. The previous JSON saver omitted several render-critical controls and never included source media or AI analysis assets, so RESET / reload + OPEN could not reproduce the editing state exactly.

Fixed / added:

- Master **Intensity / Motion / Poster Text FX** are now persistent.
- All Typography controls, clip controls, Timeline graph, FX parameters, routing, keyframes, selected layer/key, Timeline zoom/track height/scroll position, audition state and Inspector expansion state are included.
- SAVE now creates a portable **`.hypeproj`** bundle. When the source came from a user file, the original image/video is stored inside the bundle.
- Existing **Subject Mask** and **Depth Map** are stored as PNG analysis assets and rebuilt after source/project geometry is restored.
- Restore order is locked: source media first → project controls/Timeline → AI assets → derived depth/subject data → final render invalidation.
- A saved **restore fingerprint** is compared against the live state after OPEN. A mismatch is reported as an error instead of claiming that restoration succeeded.
- Local JSZip is bundled under `vendor/`, so portable SAVE/OPEN does not depend on loading the ZIP library from the network. The CDN import remains only as a fallback.
- Added `PROJECT_SAVE_RESTORE_CONTRACT.md` and `verify_project_restore.py`.
- Export pipeline protected functions remain unchanged.

### Browser round-trip test

Verified in actual headless Chromium using a fresh second app instance:

1. load an image source,
2. change Master Intensity / Motion / Type, speed, Typography and motion typography,
3. add Channel Lab and a 3-key intensity curve,
4. create Subject Mask + Depth Map caches,
5. SAVE `.hypeproj`,
6. open a completely fresh app instance with no source/layers,
7. OPEN the saved project.

Result: saved/restored project signatures were identical. Source file metadata, Master controls, Timeline layer parameters, routing, all three keyframes, selected layer/key, Subject Mask and Depth Map all matched. A second round-trip using a real MP4 also passed, including bundled video bytes, IN / OUT, Loop, Reverse, Timeline time and Slow Shutter layer parameters.

## v28.2.27

- **Low FPS / Drag Shutter** gains a new **Slow Shutter / Frame Accumulation** mode.
- Added real **Exposure Time (sec)** control from 0.033s to 0.5s. A setting of 0.25s numerically integrates the preceding quarter-second of actual layer input frames.
- Slow Shutter intentionally bypasses global Motion Flow smear: static background pixels remain stable while genuinely moving subjects spread through time.
- Exposure sample range increased to 24 and Capture FPS to 30. Temporal history sampling adapts to the requested exposure window without changing the export pipeline.
- Export pipeline remains locked and untouched.
- Recommended reference setup for the supplied 30fps / 1/4s look: **Style = Slow Shutter / Frame Accumulation, Capture FPS = 30, Exposure Time = 0.250s, Exposure Blend = 100, Exposure Samples = 16–20**.
- Camera-mode fallback no longer invents a directional blur before temporal history exists; it stays clean until real past frames are available.

## v28.2.26

### Source-first refactor of 8 existing FX

The following existing effects were rebuilt so their visible response is driven by the image entering the FX layer rather than by an unrelated full-frame overlay:

- **Glow Reactor** — source luminance distribution chooses the real highlight mask; halation / neon color is confined to those highlights.
- **Film Burn / Leak** — actual bright regions, peak luminance, nearest frame edge and highlight spread determine leak location / energy. Time only adds small drift inside the detected source region.
- **Optical Streak** — flare source is the detected bright / high-contrast region; anamorphic streaks are integrated from that highlight mask and ghosts are placed along the real source → optical-center axis.
- **Paparazzi Flash** — flash is a nonlinear exposure response based on source luminance / reflectance; recovery afterimage is restricted to actual bright regions instead of a uniform white-screen fill.
- **Scanner / Photocopier Sweep** — scanned pixels react to local luminance / edge density. Scanner electronics noise is strongest in locally flat areas, and the scan beam re-exposes the real source rather than drawing a solid bar.
- **Pulse / Impact** — the zoom remains geometric, while the flash component is now a source-luminance exposure curve instead of a full-frame color rectangle.
- **Volumetric God Rays** — new **Light Source: Auto Detect / Manual X/Y**. Auto mode finds the source highlight centroid and suppresses rays when the frame contains no convincing bright source. Depth Occluded mode is preserved.
- **Aqua Diary / Emo Retro** — average RGB, saturation, shadow fraction, edge density and highlight confidence now modulate cyan cast, contour melt, faded blacks, dirty grain, bloom and vignette.

### Shared source analysis

Added `analyzeSourceSignal()` and `paintSourceHighlightMask()` as shared low-resolution analysis primitives. They inspect the current FX input for luminance distribution, peak highlights, highlight centroid / spread, nearest frame edge, local edge contrast, average RGB, saturation, shadow fraction and warm/cool bias.

This makes stacked FX compositional: each layer analyzes the image it actually receives after earlier layers, rather than using a decorative overlay unrelated to its input.

### Regression policy

Added `SOURCE_FIRST_FX_POLICY.md` and `verify_source_first_fx.py`. The verifier checks the eight refactored FX for required source-analysis calls and prevents several legacy overlay patterns from returning.

The protected export functions were **not changed**. `verify_export_contract.py` must continue to pass.

## v28.2.25

- Added **Y2K Digicam / CCD Engine** (Analog), based on research into early-2000s compact CCD image characteristics rather than decorative overlays.
- The FX analyzes source luminance, average RGB / white-balance tendency, highlight and shadow fractions, and local edge structure before rendering.
- It models shadow-dependent CCD luminance/chroma noise, lower chroma resolution, local in-camera sharpening halos, source-dependent highlight/channel clipping, residual Auto-WB warmth, JPEG-style luma/chroma quantization, high-contrast fringe, and tiny-lens edge softness.
- Camera profiles: Pocket 4MP / Tiny 3MP / Noisy 5MP / Night Snap.
- Export pipeline protected functions are unchanged.

## v28.2.24

- Added **Aqua Diary / Emo Retro** (Analog): a more aggressively emotional retro look built around blue-green color cast, softened / partially crushed contours, dirty film grain, faded blacks, dreamy bloom, and retro vignette.
- The effect is intentionally tuned to push toward moody nostalgic short-form / diary / motel / pool-film vibes rather than neutral film emulation.
- Export pipeline intentionally unchanged; only FX definition, inspector metadata, and render branch were added.

## v28.2.23

- Added **Found Film / Natural Leak** (Analog): a new film-look FX focused on lifted shadows / milky blacks, source-derived natural light leak, soft highlight haze, film grain, and film-style color drift.
- The leak is derived from bright regions in the source image rather than a fully random overlay, so windows / backlights feel more motivated and less synthetic.
- Export pipeline intentionally unchanged. `resolveProjectSourceTime()` / offline frame lock / final composite path remain locked from v28.2.21-v28.2.22.

## v28.2.22

The v28.2.21 source-time/export pipeline is now treated as a locked baseline. This release intentionally does **not** alter the protected export functions.

### Draggable Timeline playhead

The Timeline ruler now has a visible lime playhead handle.

- click anywhere on the time ruler to jump to that project time
- drag the handle or ruler continuously to scrub to any position
- source-video preview seeks to the same canonical project/source clock
- keyboard focus on the playhead supports Left/Right by one export frame
- Shift + Left/Right moves by 0.5 seconds
- Home / End jump to Timeline start/end
- the existing vertical playhead line across FX tracks remains synchronized

The feature is isolated to Timeline UI/scrubbing. It does not introduce a second source-time mapping path.

### Export pipeline regression lock

The fixed v28.2.21 export core is protected in two ways.

1. Browser runtime `validateExportContract()` is called from `runtimePreflight()` and verifies that MP4/WebM still pass through the canonical source resolver, exact decoded-frame lock, shared final renderer and per-frame export audit.
2. `verify_export_contract.py` compares SHA-256 fingerprints of 13 export-critical functions against the reviewed v28.2.21 baseline.

Protected functions include source-time mapping, exact video seeking, offline rendering, export preflight/frame audit, MP4/WebM export, FX pixel scaling and typography scaling.

`EXPORT_PIPELINE_LOCK.md` documents the invariants that future updates must preserve.

### Project format

Project schema: **311**. This build opens v28.2.31 project files only.

---

# v28.2.21 locked export baseline

Production Tool / Source-Time Integrity Hotfix

## Priority bug

v28.2.20 fixed FX strength/color parity, but a serious remaining issue was reported: exported video content could start several seconds away from the frame shown at Timeline 0 in the Viewer.

v28.2.21 rebuilds the source-video timing contract so Viewer, paused seek, offline export, clip IN/OUT, Speed Ramp and Master Speed no longer derive source time through different call paths.

## Single project → source clock

There is now one canonical mapping:

`PROJECT TIME -> Speed Ramp -> Master Speed -> IN / OUT -> Loop / Reverse / Freeze -> SOURCE TIME`

The public internal resolver is:

`resolveProjectSourceTime(projectTime)`

The lower-level clip mapper (`sourceTimeForMappedTimeline`) is not called directly by Viewer/export code.

The previous `sourceTimeForTimeline()` path has been removed completely, preventing a future caller from accidentally applying Speed Ramp twice or omitting it.

## Viewer and Export now share exactly the same source-time resolver

Viewer seek/playback uses `resolveProjectSourceTime()`.

Offline MP4/WebM/PNG-alpha rendering also uses `resolveProjectSourceTime()`.

The offline renderer resolves the timestamp once, seeks/locks that exact source frame, promotes only that decoded frame to the video-frame cache, then renders the project frame with `lockedSourceFrame=true`.

The render pipeline is no longer allowed to independently recalculate or re-seek the source after an export frame has been locked.

## Stale paused-frame protection

The black-frame fix introduced a last-good-frame cache. That cache is useful during seek transitions, but it must never become the authoritative frame for a different Timeline time.

v28.2.21 adds:

- `videoDesiredSourceTime`
- seek generation protection
- cache timestamp validation
- paused-seek acceptance only when the decoded video time is close to the canonical expected source time
- offline-render ownership: the normal `video.onseeked` cache handler is disabled while export owns the source decoder

When Timeline/IN/OUT changes, an old cached frame may remain visible only during the very short seek transition. Once the seek settles, the cache is replaced only by the frame corresponding to the new canonical source time.

## Export source-frame lock

Every offline video frame now has three independently checked times:

1. expected source time from `resolveProjectSourceTime(projectTime)`
2. requested seek/lock timestamp
3. decoded media timestamp

Before encoding, the exporter checks that:

`expected source time == render source time == lock target`

and that the decoded frame is within approximately 1.25 source frames of the target. This tolerance permits normal codec frame quantization while still rejecting multi-frame / multi-second timing errors.

A several-second offset can therefore no longer silently complete as a successful export.

## Export progress timing display

The prominent render overlay now exposes both clocks while rendering:

`project 1.20s -> source 9.20s`

This makes IN offsets, speed changes and source progression visible during export instead of hiding the media timestamp inside the renderer.

## Post-export Viewer restore

After export, the previous Timeline position is restored using the same canonical source resolver and exact-frame lock before the normal Viewer resumes.

This prevents the Viewer from remaining on the final source frame of the export while the Timeline has already returned to its pre-export position.

## Diagnostic regression hooks

`window.__HYPE_DIAGNOSTICS__` now additionally exposes:

- `sourceClockAt(projectTime)`
- `sourceSync()`
- `seekProjectTime(projectTime)`
- expanded `summary()` source timing information

These are used for browser smoke testing and make source-clock regressions testable without exposing the mutable application state directly.

## Actual Chromium source-time smoke tests

A synthetic 12-second source video whose pixel values change continuously over time was loaded through the real file-input path in Chromium.

### Paused Viewer / IN test

IN was changed to `8.000s` while Timeline remained at `0.000s`.

Observed after seek settlement:

- project time: `0.000s`
- canonical expected source: `8.000s`
- HTML video currentTime: `8.000s`
- stable frame cache: `8.000s`

The cache initially retained the previous frame during the seek transition, then updated to exactly 8 seconds once the decode settled.

### Seek-back regression test

The synthetic source was locked at project 5 seconds and then returned to project 0 seconds.

Both transitions completed with:

- expected source time == decoded source time
- video currentTime == frame-cache time
- 0 timing error in the tested source

### Real offline export first-frame test

IN was set to `8.000s`, Timeline 0 therefore resolved to source 8 seconds, and a real locked WebM export was run through the same offline frame renderer used by the MP4 path.

The first encoded output frame was decoded with ffmpeg and compared with the source at 8 seconds:

- exported first frame YAVG: ~60.002
- source at 8s YAVG: 60
- exported first frame VAVG: ~201.022
- source at 8s VAVG: ~202.022

This confirms that the exported first visual frame is now sourced from the selected IN position rather than source 0 or a stale Viewer frame.

## MP4 verification note

The container Chromium build used for smoke testing does not expose `VideoEncoder`, so an actual H.264 encode cannot be completed in this environment.

MP4 and WebM both call the same `renderOfflineFrame()` before encoding. The source-time resolver, exact source lock, stable-cache promotion and per-frame timing audit therefore execute before the format-specific encoder.

The user's Mac/Chrome H.264 test remains the final verification for the MP4 container itself.

## Existing v28.2.20 export-integrity protections retained

- exclusive export render lock
- Viewer and library preview suspended during export
- single `renderProjectFrame()` / `renderMain()` final-composite path
- per-frame Timeline FX graph audit
- project-state fingerprint invariant
- Subject/Depth dependency preflight
- resolution-invariant Typography design coordinates
- resolution-normalized pixel-space FX
- deterministic seeded FX noise during rendering
- prominent full-screen export progress UI
- even H.264 output dimensions
- AI Source Version / Request ID / AI Epoch guards
- GPU Y-orientation fix

## Project schema

- Current-only schema: **309**
- This build opens v28.2.29 project files only.
- Portable project extension: **`.hypeproj`** (ZIP container with `project.json`, optional source media, optional Subject Mask / Depth Map).

## Static QA

PASS:

- extracted JavaScript `node --check`
- 53 FX definitions / 53 unique IDs
- 212 DOM IDs / no duplicates
- 287 named functions / no duplicates
- schema 308
- Project Restore Contract PASS
- real Chromium image project round-trip PASS
- real Chromium video project round-trip PASS
- no `sourceTimeForTimeline` references remain
- canonical `resolveProjectSourceTime()` present
- Export uses a locked source frame after exact seek
- normal seek handler is bypassed during offline rendering
- source-clock functions included in runtime preflight
- final Typography composite appears exactly once
- H.264 even-dimension helper preserved
- GPU `UNPACK_FLIP_Y_WEBGL=false` preserved
- AI async guards preserved

## Recommended user smoke test

Use the same source that showed the ~8 second discrepancy:

1. Set a visually obvious IN point.
2. Stop at Timeline `00:00.00` and confirm the Viewer frame.
3. Export 10 seconds as Full / MP4 / 30fps.
4. Compare exported frame 0 with Viewer Timeline 0.
5. During export, confirm the overlay begins with the expected `project 0.00s -> source X.XXs` value.

A timing mismatch larger than normal source-frame quantization should now stop export instead of producing a silently shifted file.


## Source-first FX policy

For photographic / analog / optical effects, new work should prefer **source-derived transforms** over decorative overlays. Analyze luminance, color balance, edges, motion, depth, highlights, or temporal history first; then derive the effect response from those features. Random textures may be used only as a secondary physical-noise model and must remain deterministic per timeline time for Preview / Export parity.

`Y2K Digicam / CCD Engine` follows this policy: no date stamp, dust frame, fake UI, or stock texture is composited over the image.