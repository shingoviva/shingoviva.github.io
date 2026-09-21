# Native Export Test Report — v28.2.35

## Static release verification

- JavaScript `node --check`: PASS
- Python helper `py_compile`: PASS
- Export Contract: PASS — 13 protected Browser Export functions unchanged
- Native Export Contract: PASS — 15 checks
- DOM IDs: 217 unique
- Named functions: 313 unique
- FX definitions: 53

## Native helper protocol smoke test

Environment: Linux development container, FFmpeg 7.1.5. VideoToolbox is not available on Linux, so the helper correctly selected `libx264` fallback.

Test flow:

1. `/health`
2. `/start` — 64×64, 30fps, 3 frames
3. Three raw RGBA frame POSTs in exact order
4. `/finish`
5. `ffprobe` validation

Result:

- codec: H.264
- pixel format: yuv420p
- resolution: 64×64
- frame rate: 30/1
- frame count: 3
- protocol frame-order / byte-count validation: PASS

## Mac-only acceptance test still required

The target Mac should confirm:

- helper reports `h264_videotoolbox`
- completed MP4 visually matches Browser Export for the same project/time range
- Export Profiler phase percentages are sensible
- output is created in `~/Downloads/HYPE_FORM_EXPORTS/`
- measured total export time improves on Browser Export for the user's normal project