# NATIVE EXPORT CONTRACT — v28.2.35

1. Native export is optional. Browser Export is mandatory fallback.
2. Native export must consume frames produced by the existing protected `renderOfflineFrame()` → `renderProjectFrame()` path.
3. Native helper must not implement, approximate, reorder, or omit Visual FX.
4. Export project-signature mutation guard and per-frame FX graph audit remain active.
5. Exact source-frame lock remains active for video sources.
6. Native helper binds to `127.0.0.1` only.
7. H.264 encoder preference on macOS is `h264_videotoolbox`; software H.264 is diagnostic fallback only.
8. Helper absence or helper/FFmpeg failure must not make MP4 export unavailable: automatic Browser fallback is required.
9. Native MP4 dimensions must remain even and output `yuv420p`.
10. Profiler must distinguish browser render work from readback/native transfer/finalization sufficiently to identify the dominant bottleneck.
