# FINAL LOOK / MASTER OPTICS CONTRACT — v28.2.29

The Final Look stage is a single post-composite correction stage shared by Live Viewer, PNG capture, MP4 export, and WebM export through `renderProjectFrame()`.

## Invariants

1. Final Look is applied only once, after Timeline FX, audition FX, Typography, and Strobe are composited.
2. Master temporal feedback stores the pre-Final-Look composite. This prevents Exposure / Saturation / WB corrections from accumulating frame-over-frame.
3. Exposure is expressed in EV and applied in linear-light space (`2^EV`).
4. The stage supports Exposure, Contrast, Highlights, Shadows, Saturation, Temperature, and Tint.
5. The controls are part of portable `.hypeproj` save / restore and undo / redo snapshots.
6. The same state values are included in `exportProjectSignature()` so changing Final Look during offline export invalidates the export.
7. Alpha-material export remains a material-generation path and is intentionally not treated as the full final composite.

Run `python verify_final_look.py` after changes touching render order, project persistence, Final Look controls, or export state.