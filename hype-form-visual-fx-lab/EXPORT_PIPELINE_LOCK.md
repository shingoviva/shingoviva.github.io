# EXPORT PIPELINE LOCK

Baseline: **v28.2.21 source-clock / final-composite pipeline**

This is a maintenance guard. Ordinary UI, Timeline, Inspector and FX updates should not rewrite the protected export core.

## Required invariants

1. One source clock only:
   `PROJECT -> Speed Ramp -> Master Speed -> IN/OUT/Loop/Reverse/Freeze -> SOURCE`
2. Viewer and Export resolve source time through `resolveProjectSourceTime()`.
3. Offline video export locks an exact decoded source frame before rendering it.
4. Preview/Capture/Export share `renderProjectFrame()` / final-composite behavior.
5. Each export frame audits expected vs actually applied FX layer IDs and order.
6. Project state is fingerprinted; mutation during export aborts the export.
7. FX pixel-space strength is normalized through `fxPixelScale()`.
8. Typography sizing is normalized through `typographyPixelScale()`.
9. MP4 and WebM both render frames through `renderOfflineFrame()`.
10. H.264 output dimensions remain even.

## Protected functions

- `sourceTimeForMappedTimeline`
- `resolveProjectSourceTime`
- `waitForVideoSeek`
- `waitForExactVideoFrame`
- `renderProjectFrame`
- `renderOfflineFrame`
- `validateExportPreflight`
- `validateExportFrameAudit`
- `exportMp4FramePerfect`
- `exportWebmFallback`
- `exportVideo`
- `fxPixelScale`
- `typographyPixelScale`

Run `python3 verify_export_contract.py` after every update. A failure means an export-critical function changed and must be deliberately re-verified before release.

The browser runtime also calls `validateExportContract()` from `runtimePreflight()` so obvious bypasses of the locked pipeline are surfaced immediately.