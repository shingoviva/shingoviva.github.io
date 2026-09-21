# NATIVE FAST EXPORT CONTRACT — v28.2.35

This contract adds a native macOS H.264 encoder without replacing the locked browser export core.

## Required invariants

1. Browser Export remains available and its 13 protected functions remain byte-for-byte unchanged from v28.2.34.
2. Mac Fast Export must render every frame through the existing `renderOfflineFrame()` path before native encoding.
3. The native helper accepts raw RGBA only from loopback/browser-approved origins and binds to `127.0.0.1` only.
4. Native mutation endpoints require the random helper token returned by `/health`.
5. The browser cannot choose an arbitrary filesystem path. The helper owns output naming and writes only to its export directory.
6. Frame count, frame order, byte count, dimensions and FPS are validated before FFmpeg accepts the stream.
7. On macOS the helper prefers `h264_videotoolbox`; helper absence or any Native export failure automatically falls back to the protected Browser Export.
8. The Export Profiler reports Render / Readback / Feed+Encode / Finalize separately.
9. Native failure must not corrupt the project/session state; Viewer time and playback state are restored after the attempt.
10. PNG Alpha and WebM remain on their existing export paths.

## Performance interpretation

`RENDER` includes exact source-frame locking and HYPE FORM compositing. If it dominates, FFmpeg is not the principal bottleneck and future work should optimize source decode/render rather than the encoder.

`FEED / ENCODE` includes local RGBA transport and FFmpeg backpressure. If it dominates, transport or encoder settings are the next target.