# HYPE FORM — Signal Simulation Contract

Baseline: v28.2.32

Physical / analog-signal FX must damage or transform the source signal itself. They must not substitute decorative white bars, rings, or full-frame washes for the phenomenon being simulated.

## Analog Signal

`Signal Dropout` is modeled in the scanline signal domain:

- horizontal line detail energy and chroma energy are sampled from the incoming frame;
- defect occurrence is deterministic at a fixed project time;
- a damaged segment loses Y/C information rather than receiving a white overlay;
- missing signal is partially reconstructed from a neighboring previous scanline, approximating dropout compensation;
- chroma is attenuated more strongly than luma in damaged segments;
- residual RF-like noise is injected into the damaged signal;
- CRT / interlace scanline appearance is multiplicative modulation of source pixels, not painted black stripes;
- VHS head-switch damage is source-line replacement / timebase shift / chroma loss near the lower raster, not white bars.

## Tape Deck / Generation Loss

- Tape dropout uses local detail / chroma stress plus a deterministic tape-defect field.
- Missing tape signal uses previous-scanline compensation and chroma attenuation.
- Crease damage modifies source sampling position, luma bandwidth, and chroma integrity.
- Head-switch damage replaces / shifts source signal and adds signal noise in the lower raster.
- Generation loss is applied in luma/chroma signal space instead of a solid screen-color wash.
- Temporal ghosting remains source-derived from the layer's own previous frame.

## Physical fallbacks

If a GPU implementation is unavailable, the fallback must preserve the same physical idea:

- `Shockwave` CPU fallback radially remaps source pixels; it must never draw a white ring as a substitute.
- `Advanced Bloom` CPU fallback extracts actual source highlights and blurs that mask; it must never bloom the whole source indiscriminately.

## Regression

`verify_source_first_fx.py` checks these signal-domain paths and rejects known legacy overlay patterns.