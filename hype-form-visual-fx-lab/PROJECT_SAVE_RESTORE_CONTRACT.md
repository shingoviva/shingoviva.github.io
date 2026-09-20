# HYPE FORM Project Save / Restore Contract

Baseline: **v28.2.34 portable session v2**. Project schema remains **313** so v28.2.33 portable projects stay loadable.

SAVE is a work-session snapshot, not a settings preset.

A portable `.hypeproj` must preserve:

- Master controls, including Intensity / Motion / Poster Text FX.
- Final Look / Master Optics: Exposure, Contrast, Highlights, Shadows, Saturation, Temperature, Tint.
- Composition and typography controls.
- The selected local font **including its font file bytes** when that font came from the local-font picker.
- Project length and current playhead time.
- Video IN / OUT / Loop / Reverse / Freeze.
- Every Timeline FX layer, order, enabled state, routing, blend/mix, parameters, keyframes, active curve, selected layer/key.
- Timeline zoom / track height / scroll position.
- Source-media identity; when the source came from a user file, the file is bundled into the project.
- AI Subject Mask and Depth Map when they exist, including a lightweight content fingerprint for each bundled analysis canvas.
- Current temporary audition FX and Inspector expanded state.

## Save snapshot rule

Mutable source / font / mask / depth assets are snapshotted before asynchronous ZIP work begins. A single `.hypeproj` must not mix the source from one moment with AI analysis from a later moment.

## Restore order is locked

1. Decode the project bundle.
2. Validate schema, Timeline graph, unique layer IDs, referenced FX and the saved project metadata fingerprint **before replacing the current source**.
3. Restore a bundled local font if the project uses one.
4. Restore bundled source media and wait for decoded media readiness.
5. Restore project controls and Timeline graph. `nextLayerId` is normalized to at least `max(existing layer ID)+1`, and stale selected key/layer references are cleared.
6. Restore AI mask/depth assets after project geometry is known.
7. Verify the restored analysis canvases against their bundled fingerprints, then rebuild derived depth planes / subject anchor.
8. Compute a post-load project fingerprint and require it to equal the saved fingerprint.
9. Treat a successful OPEN as a new session boundary: clear Undo/Redo rather than offering a cross-project Undo that cannot safely restore source-media bytes.

A project that fails any validation or final fingerprint check must not report a successful restore.

Project SAVE / OPEN and source replacement are unavailable while an Export render lock is active.

Export rendering is intentionally outside this contract and remains protected separately by `EXPORT_PIPELINE_LOCK.md`.