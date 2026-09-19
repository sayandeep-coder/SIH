# Hyperframes Composition Brief: India Airfare Index (APIx)

## Objective
Create a short launch-style brag video for India Airfare Index (APIx).

## Output
- Composition directory: `brag-output/composition/`
- Rendered video: `brag-output/brag.mp4`
- Format: landscape — 1920x1080
- Duration: 20 seconds

## Source Material
- Project root: /Users/sayandeep/SIH
- Primary files read: frontend/app/page.tsx, frontend/app/airfare-index/page.tsx, frontend/app/globals.css, frontend/components/Shell.tsx, README.md, frontend/package.json
- Product name: India Airfare Index
- Tagline / strongest claim: "Nothing on the dashboard is fake or hardcoded — every number comes from the database via the API."
- Key UI or visual moment to recreate: the navy sidebar with pulsing live-status dot + monospace telemetry bar ("SOVEREIGN PIPELINE: ACTIVE SURVEILLANCE"), the KPI grid, the Latest Fare Quotes table, and the methodology ribbon on the Airfare Index detail page.
- Copy that must appear verbatim:
  - "SOVEREIGN PIPELINE: ACTIVE SURVEILLANCE"
  - "Airfare Price Index"
  - "MoSPI / GoI CPI Baseline"
  - "WEIGHTED MODIFIED LASPEYRES"
  - "Nothing on this dashboard is fake."
  - "Every number comes from the pipeline."

## Creative Direction
- Tone preset: polished
- Creative direction: national data-surveillance command terminal — restrained, serious, institutional
- Interpretation: Confidence through restraint. Few scenes, longer holds, hard cuts instead of flashy transitions. Monospace typography does the talking. No jokes, no winking at the camera — the seriousness itself is the hook.
- Angle: This isn't a mock dashboard with placeholder numbers — it's presented as a national surveillance terminal for airfare inflation: dark command-center UI, live telemetry, a real pipeline (Playwright → Celery → Postgres → index math). Treat it with total institutional seriousness, like classified infrastructure, and let the reveal be "no fake numbers — this is a real pipeline nerds built."
- Hook: Black frame. A single monospace line types in: "SOVEREIGN PIPELINE: ACTIVE SURVEILLANCE". A cursor blinks. Hard cut to the dashboard.
- Outro / punchline: "Nothing on this dashboard is fake." / "Every number comes from the pipeline." then logo mark.
- Avoid:
  - Generic SaaS language
  - Abstract filler visuals
  - Unrelated visual redesign
  - Playful/bouncy easing (this is `polished`, not `default`)

## Visual Identity
- Background: #f7f9fd (light dashboard bg), #0f172a (navy sidebar/terminal bg)
- Text: #102238 (ink), #cbd5e1 (sidebar text), #94a3b8 (muted mono labels)
- Accent: #103aa5 (blue), #07583e (green success), #63e6be (live pulse dot)
- Display font: IBM Plex Sans (Google Fonts) or closest safe fallback
- Body/mono font: JetBrains Mono (Google Fonts) or closest safe fallback
- Visual references from the project: navy sidebar with plane icon + wordmark, pulsing green-ish live dot, monospace telemetry strip, KPI card grid, data table with corridor/airline/fare/window columns, methodology ribbon banner

## Storyboard
Use the storyboard in `brag-output/brag-plan.md` as the creative contract.

Scene summary:
1. The hook — 3s — black frame, "SOVEREIGN PIPELINE: ACTIVE SURVEILLANCE" types in character by character, cursor blink, live-pulse dot appears
2. Dashboard reveal — 4s — hard cut to Overview dashboard; navy sidebar slides in from left; 5 KPI cards arrive one by one
3. Live data populating — 5s — fare quote table rows land one by one; "Current Airfare Index" number counts up to final value
4. Methodology + scrape flow — 5s — Airfare Index detail page methodology ribbon holds; a scrape-run status flips RUNNING → SUCCESS with ingested count
5. Outro / punchline — 3s — black frame, two typed lines, then logo mark fade-in

## Audio
- Audio role: sparse professional accents over a restrained music bed
- Audio arc: near-silent open under the hook typing, rises to ~0.3 volume on the dashboard reveal, holds steady through the data scenes, fades over the final 1.5s
- Music: assets/music/happy-beats-business-moves-vol-12-by-ende-dot-app.mp3 (trim to 20s; 109.96 BPM)
- Music treatment: data-volume ramps 0.05 → 0.3 over scene 1→2, holds ~0.28-0.3 through scenes 2-4, tweens to 0 over the last 1.5s of scene 5
- Music cue guidance: cue JSON at assets/music/cues/happy-beats-business-moves-vol-12-by-ende-dot-app.music-cues.json. Strong cues in the 0-20s window: 8.74s, 13.11s, 17.47s, 18.56s. Scene boundaries at natural timing (3s/7s/12s/17s) sit 1.1-1.7s from the nearest strong cues — too far for a ±0.15s lock without compressing scene durations and hurting the reading-time floor. Decision: keep scene durations as planned in brag-plan.md (readability wins); use the beat grid only as a loose backbone for the table-row and KPI-card stagger timing within scenes 2-3, not for scene-cut locks. If Hyperframes finds a low-cost adjustment (±0.3s scene shift) that lands a cut closer to a strong cue without cutting text below its reading floor, it may apply it, but this is optional, not required.
- Audio-reactive treatment: none — keep visuals deterministic and calm, matching the polished/institutional tone. Do not implement RMS/frequency-based visual modulation for this video.
- Audio-coupled moments:
  - Scene 1 hook typing — each character typed pairs with a randomized `assets/sfx/keyboard/keypress-*.wav` (8 files available: 001,003,005,007,009,011,013,015)
  - Scene 4 scrape-run SUCCESS flip — `assets/sfx/interface/drop_001.ogg` at the moment the badge changes
  - Scene 5 outro typing — same randomized keypress SFX as scene 1
  - Scene 5 logo landing — `assets/sfx/interface/bong_001.ogg`, quiet, restrained
- SFX selection guidance: Per audio.md polished-tone guidance — 2-3 very subtle SFX total (plus the typing layer, which is a distinct textural element, not a "reveal" SFX). Nothing aggressive. `bong_001` only once, at the very end.
- SFX analysis guidance: skills/brag reference (`sfx-analysis.md`) recommends low/medium HF-risk files for polished/repeated moments — the selected files (drop_001, bong_001, keypress set) already satisfy this; no further substitution needed.
- Exact SFX choice: as listed above; Hyperframes may substitute an equally restrained file from the same copied set if timing requires it, but should not introduce new SFX families.
- Audio files: already copied into `brag-output/composition/assets/music/` and `brag-output/composition/assets/sfx/{interface,keyboard}/`.

## Hyperframes Instructions
Load the composition-building Hyperframes domain skills — `hyperframes-core`, `hyperframes-animation`, `hyperframes-creative`, `hyperframes-keyframes`, `hyperframes-cli`. This is a standalone top-level `index.html` composition (no sub-compositions needed given the scene count and complexity — build monolithic with one `.clip` section per scene, per `hyperframes-core` → composition-patterns.md guidance for simpler projects). Prefer native Hyperframes conventions over anything in the brag skill docs.

Requirements:
- Show at least one real UI, copy, or visual element from the source project (the dashboard sidebar, KPI grid, fare table, and methodology ribbon all qualify).
- Keep all text readable in the final render — respect the reading-time floor (short label ~0.8s settled; sentence ~0.3s/word).
- Keep the video within 15-25 seconds (target exactly 20s).
- Include the planned music/SFX layer as described above.
- Treat music cue metadata as optional timing hints — ignore cues that hurt readability, scene pacing, or the product story.
- Use SFX to support motion and interaction as described in Audio-coupled moments above.
- Honor the planned music treatment (fade-in under hook, hold, fade-out at outro).
- No audio-reactive visual treatment for this video (explicitly declined above for tone reasons).
- Use local copied assets for all audio.
- Run `npx hyperframes check` before render — this is brag's single gate.
