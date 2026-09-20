# CORE STABILITY AUDIT — v28.2.34

This contract protects recent fixes that sit outside the older Export / Project / Viewer contracts but are important to production behavior.

## Required invariants

1. **Export mutation signature covers render-critical state.** Master Intensity / Motion / Type, source generation, Subject/Depth analysis generation, Final Look, typography, source range, routing graph and composition state must participate in `exportProjectSignature()`.
2. **Source replacement cannot happen during export.** `processSourceFile()` and Project OPEN must reject source mutation while the export render lock is active.
3. **GPU shader failures are sticky for the session.** A shader that failed compilation must fall back to Canvas without recompiling and failing on every frame.
4. **WebGL context loss is recoverable.** Context loss switches to Canvas fallbacks; restoration clears cached GL resources and allows GPU initialization again.
5. **Live AI cannot be forced under load.** The scheduler uses no idle-callback timeout and re-checks source version / timing budget before inference.
6. **Slow Shutter does not pay for Motion Flow.** `dragShutter` style `slow` uses temporal frame accumulation only.
7. **Paused video letterbox/background cache is refreshable.** Changing background color while paused refreshes the cached video composition rather than leaving stale bars.
8. **Dynamic script loading is retryable.** A failed script element is removed; an in-flight existing script is awaited rather than being assumed loaded.
9. **Runtime preflight knows about the v28.2.34 project validators.** Project document validation and local-font installation must be present in required-function checks.