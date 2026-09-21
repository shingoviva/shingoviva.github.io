# HYPE FORM / Visual FX Lab v28.2.35 — Mac Fast Export

v28.2.35 adds an optional local Native Export Helper. The existing Browser Export remains the safety fallback.

## Architecture

HYPE FORM UI  
→ protected `renderOfflineFrame()`  
→ protected `renderProjectFrame()`  
→ raw RGBA frame  
→ local Mac Native Export Helper  
→ native FFmpeg  
→ `h264_videotoolbox` when available  
→ MP4

The helper does **not** recreate FX or color processing. The browser still creates every final-composite frame, preserving Preview/Export look parity and the existing Export Pipeline Contract.

## Why this can be faster

Browser MP4 currently renders each locked frame and also performs WebCodecs/Mediabunny encoding in-browser. Native mode moves H.264 compression/container work to FFmpeg and, on Apple Silicon / supported Intel Macs, prefers VideoToolbox hardware encoding.

Native FFmpeg cannot remove the cost of:
- exact source-frame seeking / decode lock
- temporal FX rendering
- GPU/Canvas render work
- GPU → CPU readback required to hand RGBA frames to the helper

That is why v28.2.35 includes an Export Profiler. It reports Frame Render, Readback, Native Pipe/Encode, Finalize, and Total time. If Frame Render dominates, the next optimization target is the renderer rather than FFmpeg.

## First-time setup

1. Install FFmpeg if needed:
   `brew install ffmpeg`
2. In Finder, right-click `START_MAC_FAST_EXPORT.command` and choose Open the first time if macOS blocks it.
3. Keep the Terminal window open. It opens HYPE FORM at:
   `http://127.0.0.1:48735/`
4. In Export → MP4 Engine choose:
   - **Auto**: use Mac Native when helper is detected, Browser otherwise.
   - **Mac Native**: prefer helper; if unavailable or an export fails, the app automatically retries with Browser Export.
   - **Browser**: always use the existing protected WebCodecs path.
5. Native MP4 files are saved to:
   `~/Downloads/HYPE_FORM_Exports/`

## Important behavior

- GitHub Pages remains usable. Because the helper is local, use the localhost page opened by the command file for Native Export.
- Browser Export remains available without Python/FFmpeg/helper.
- The 13 protected export functions remain unchanged in v28.2.35.
- Project mutation protection, source-time locking, FX layer audit, final look, typography scaling, and resolution normalization remain active.
- Native failures are treated as recoverable and fall back to Browser Export.

## Profiler interpretation

If **Frame Render** is the majority, FFmpeg is not the main bottleneck. Investigate exact video seek/decode, temporal FX, Canvas/WebGL work, or other per-frame render costs.

If **Readback** is large, GPU → CPU transfer is the bottleneck. A later native/shared-memory or WebCodecs VideoFrame path may help.

If **Native Pipe / Encode** is large, tune bitrate, frame transport, and VideoToolbox settings.

If **Finalize** is large, inspect FFmpeg flush/container finalization or filesystem speed.
