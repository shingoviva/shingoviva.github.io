# VIEWER LAYOUT CONTRACT

Baseline: **v28.2.33**

The Live Viewer is an editing viewport. Its visible geometry must be independent from render-performance decisions.

## Required invariants

1. Internal Preview proxy resolution (`W/H`) may change without changing the visible Viewer box.
2. `fitViewerStage()` must use the project/source aspect (`activeProjectRatio()`), never proxy `W/H`.
3. `resizeProjectCanvases()` is render-buffer-only and must not call `fitViewerStage()`.
4. Viewer CSS width/height must not animate when render quality changes.
5. Viewer size may change only after a real layout/aspect event: window or workspace-panel resize, Focus Preview, or project/source aspect change.
6. ResizeObserver callbacks must be coalesced and must not repeatedly write identical dimensions.
7. Preview FPS tier, Auto Preview resolution, heavy FX, AI analysis, and temporal-buffer pressure must not alter Viewer DOM geometry.
8. Export output geometry is independent and must remain unchanged.