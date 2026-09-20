# HYPE FORM — Source-First FX Policy

Baseline: v28.2.32

HYPE FORM visual effects should transform the image because of information found in the image, its motion, depth, or temporal history — not merely because a decorative overlay happens to be scheduled at that time.

## Core rule

For optical / film / camera / light effects, every important visible response should have a causal input:

- luminance / highlight location
- shadow distribution
- local contrast / edges
- source color / white-balance tendency
- motion vectors
- AI depth / subject masks when relevant
- frame history for temporal effects

Synthetic artifacts are allowed when they model a physical or signal process, but their placement / intensity should be driven by source measurements whenever that process requires a source cause.

## Anti-patterns

Avoid:

- a lens flare whose light source moves only from `sin(time)` when no bright source exists
- a full-frame white flash painted over every pixel with equal strength
- a light leak placed at an arbitrary screen edge independent of source highlights
- bloom / halation generated from a full-frame color wash instead of a highlight mask
- random scanner damage that ignores local tone / edge structure

## Audited FX

The following FX are protected by `verify_source_first_fx.py`:

- Glow Reactor (`bloom`)
- Film Burn / Leak (`lightLeak`)
- Optical Streak (`lensFlare`)
- Paparazzi Flash (`paparazziFlash`)
- Scanner / Photocopier Sweep (`scannerSweep`)
- Pulse / Impact (`pulseZoom`)
- Volumetric God Rays (`godRaysPro`)
- Aqua Diary / Emo Retro (`aquaDiary`)
- Analog Signal (`analogSignal`)
- Tape Deck / Generation Loss (`tapeDeck`)
- Shockwave CPU fallback (`shockwavePro`)
- Advanced Bloom CPU fallback (`advancedBloom`)

## Regression tests

Future updates should preserve these behavioral expectations:

1. A dark frame without a bright source should not produce a strong Lens Flare, Film Leak, or Auto God Rays.
2. A bright window / lamp near an edge should attract Film Leak and Auto God Rays toward that real highlight.
3. Optical Streak ghosts should be placed along the real source-to-optical-center axis.
4. Paparazzi Flash and Pulse / Impact should change exposure according to source luminance, not paint a uniform full-frame rectangle.
5. Scanner processing should react to local luminance / edge structure.
6. Aqua Diary should adapt cyan, softness, fade, grain, and bloom to the scene statistics.
7. Analog / tape dropout must damage Y/C signal content and use source-line compensation instead of painted white streaks.
8. Physical GPU fallbacks must transform source pixels; they must not replace the effect with decorative geometry.
9. Source-first analysis must remain deterministic for a fixed source frame / project time.

## Export rule

This policy is separate from `EXPORT_PIPELINE_LOCK.md`. Source-first FX work must not modify the protected export timing / final-composite functions unless a dedicated export regression task explicitly requires it.