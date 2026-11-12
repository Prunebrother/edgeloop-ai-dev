# Optional portrait animation (review build)

> **Status 2026-11-12:** enabled for real-gameplay testing. The catalog flag is `true`
> and all 48 built-in expressions declare a WebM idle clip in
> `Character_Art/<Name>/animations/` (8 s, 30 fps, VP9, silent; produced by the
> offline pipeline in `~/Work/edgeloop-animation-pipeline`). No MP4 fallbacks are
> shipped (+83 MB). Browsers without VP9 fall back to the PNG. The text below describes
> the original default-off review build. Rollback: set the flag to `false`. Known
> issue: background warping near the figure, see [BACKLOG.md](BACKLOG.md) PA-1.

The default remains PNG-only. `src/assets/characters/manifest.json` has
`presentation.animated_characters_enabled: false`. No runtime clips are declared
or shipped in this change. Nova's independently produced clip needs a separate
asset review before a local preview.

After review, a curated character may optionally have a sibling map alongside its
unchanged `expressions` image map:

```json
"animations": {
  "neutral": {
    "webm": "/Character_Art/Nova/neutral.webm",
    "mp4": "/Character_Art/Nova/neutral.mp4"
  }
}
```

Only the resolved identity's exact selected canonical expression is eligible.
Neutral video is never substituted for an unanimated Happy expression. WebM/VP9
is preferred, then MP4/H.264, then the existing expression image and neutral-image
fallback. Static custom portrait packages need no new fields and never inherit
clips from their underlying built-in model.

Declared clips must be curated same-origin files beneath `/Character_Art/`, with
plain alphanumeric/underscore/hyphen path segments, matching `.webm` or `.mp4`
extensions, and a canonical expression key. Both static hosts and the public
export restrict access/inclusion to declarations. Release export rejects missing
or unsafe declared clips. The original 48-PNG inventory remains mandatory.
There is no user-video upload API, directory scan or guessed-file probe.

`CharacterPresentation` owns media elements, readiness, timeout, failure fallback,
visibility and disposal. Its existing revision counter/layers handle all image /
video transitions. Video must start muted and supply a first decoded frame before
admission. Same-identity outgoing artwork remains until replacement is ready;
other identities clear immediately. A failed active video is paused and retains its last frame
while replacement loads. At most one decoder is retained in steady state and two
in a handoff. A superseding update disposes the previous pending/outgoing media.
There are no Player, observer, Director, card, inference or hardware callbacks.

Hidden panels, Theater occlusion, background documents, pagehide, fullscreen exclusion and reduced
motion suppress playback; showing the panel prepares only its latest state.
The existing layout reports Theater occlusion through a presentation-only panel
attribute; the renderer never calls the Player. Reduced motion and flag disable
return to static artwork. Missing/error/autoplay
failures are bounded in a 64-entry per-expression/URL set for this renderer's
lifetime; repeated activity updates never probe again. Reload after installing or
replacing a failed clip at the same URL. New URLs can be tried immediately.

The enabled fade is 350 ms (380 ms layer cleanup); disabled PNG behavior retains
250 ms / 280 ms. Existing fit/position and stage dimensions are preserved.
Reduced-motion CSS still disables transitions. Videos have an accessible label,
no controls, and no audio use. Source assets must have no audio track; verify
codec/profile, dimensions, FPS, duration and loop quality during asset review.
Production targets are 2:3, 1024×1536, 30 FPS, four-second seamless neutral idle.
The tiny test clips deliberately do not meet those production dimensions/timing.

## Validation

Use the existing environment; no model or hardware is needed:

```sh
node --test --test-isolation=none tests/fork/portrait-animation.test.mjs
.venv/bin/python -m pytest -q tests/fork/test_portrait_animation_assets.py
PORTRAIT_BROWSER_REPORT=/tmp/portrait-browser node tests/fork/portrait-animation-browser.mjs
```

The browser fixture intercepts all requests and uses the real renderer and Player
with procedural test clips. It covers the 48 default-off PNGs, real VP9/H.264
readiness, failures, autoplay rejection, rapid switching, CSS-hidden panels,
reduced motion, controlled document-hidden input, decoder-source bounds, flag
disable and Player counters. It requires functional Playwright Chromium. The
controlled document-hidden test is not an OS background-tab test. Run the
existing character, builder, player-interaction and AI-settings browser fixtures
as well, on an environment permitting loopback servers and Chromium launch.

Rerun the full Python, companion JS and engine suites. Do not use one shared
single-process environment across *all* engine files: those tests replace global
storage/document objects. The documented `npm test` uses per-file isolation.
A per-file fresh-process run with `--test-isolation=none` is also useful when
collecting nested counts. Compare CPU/GPU/memory on target hardware before
accepting production assets; source-count assertions are not decoder profiling.

## Rollout and rollback

Keep the renderer change and production assets separate. Review the code with
flag off and no runtime videos first. Review Nova's neutral clip, then declare it
only in a local preview and enable the catalog flag there. Validate events,
framing, hidden/visible transitions and resource measurements before expanding
to Celeste, Evelyn and Daisy. Additional emotions and custom video ingestion are
separate work. Revert the flag to false and reload to restore PNG-only rendering;
no database, custom schema or AI configuration migration is involved.
