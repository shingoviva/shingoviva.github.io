# PREVIEW STABILITY CONTRACT

Baseline: **v28.2.34**

The Live Viewer must prioritize continuous decoded-video presentation, stable frame pacing and stable editor geometry over background work.

## Required invariants

1. **Presented video frames drive the cache.** On browsers with `requestVideoFrameCallback()`, the Viewer cache is refreshed from actual presented frames instead of polling/copying the video element every render RAF.
2. **No decoded-frame-counter gating.** `getVideoPlaybackQuality().totalVideoFrames` must not decide whether a Viewer frame is refreshed; implementations may update that counter irregularly.
3. **No drift-triggered seek loop during normal forward playback.** Hard seeks are only allowed for explicit/discrete clock discontinuities (play/scrub sync, project wrap, selected source-range wrap). Ordinary drift is handled with gentle playback-rate correction.
4. **Stable frame pacing.** Lightweight playback stays at 60 fps. Adaptive pacing uses only 60/30 fps with sustained-load hysteresis; no 45 fps tier is allowed. RAF timing must include enough tolerance that a 60 Hz `~16.67 ms` callback does not miss a `16.7 ms` boundary.
5. **No mid-playback canvas-resolution rebuilds.** Auto Preview may choose a different proxy while playing, but resize is deferred to a playback boundary.
6. **Layer feedback canvases are lazy.** Full-frame previous-frame buffers are allocated only by FX that consume feedback.
7. **Live AI remains outside the render hot path and budget-gated.** Scheduling must be source-version guarded, re-check the live timing budget immediately before inference, and must never use a forced `requestIdleCallback` timeout that can fire under load.
8. **Slow Shutter / Frame Accumulation does not require Motion Flow.** Its blur comes from real temporal history. Motion Flow is only requested for the Natural / Long Tail drag-shutter styles.
9. **Library preview cards remain idle-only during Timeline playback.**
10. **Proxy resolution must not resize the Viewer DOM.** `resizeProjectCanvases()` may rebuild internal render buffers, but it must never change Viewer CSS width/height.
11. **Viewer aspect comes from project geometry, not proxy rounding.** Display sizing uses `activeProjectRatio()` rather than internal `W/H`.
12. **No animated Viewer width/height.** Performance adaptations must never visibly pulse the editing layout.
13. **Export behavior remains independently locked.** Always run `verify_export_contract.py` after Viewer work.

## Regression symptoms this contract is designed to prevent

- repeated micro-freezes at fixed or near-fixed points even with no FX,
- periodic hard seeks caused by a small timeline/video clock difference,
- displayed video frames updating in bursts because a decoded-frame counter is stale,
- 60 Hz playback alternating between 16.7 ms and accidental ~33 ms gaps,
- AI inference being forced onto the main/GPU path during a busy playback interval,
- heavy canvas reallocations interrupting the Viewer,
- the preview box visibly changing size when Auto Preview changes proxy resolution.