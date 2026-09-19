# Brag Plan: India Airfare Index (APIx)

## What is this app?
A live, real-data price index for Indian domestic flights — it scrapes Google Flights, cleans and validates the data, and computes a CPI-style inflation index for airfares, the way MoSPI tracks consumer prices, but for flights.

## The angle
This isn't a mock dashboard with placeholder numbers — it's presented as a national surveillance terminal for airfare inflation: dark command-center UI, live telemetry, a real pipeline (Playwright → Celery → Postgres → index math). The angle: treat it with total institutional seriousness, like classified infrastructure, and let the reveal be "no fake numbers — this is a real pipeline nerds built."

## Hook (first 2-3 seconds)
Black frame. A single monospace line types in: `SOVEREIGN PIPELINE: ACTIVE SURVEILLANCE`. A cursor blinks once. Then hard cut to the dashboard, navy sidebar sliding in from the left.

## Key moments (the middle)
- The KPI grid populating: "Current Airfare Index" ticking up to its real value, "Data Freshness" reading in live minutes.
- The Latest Fare Quotes table — rows of real corridor/airline/fare data landing one by one (DEL-BOM, BLR-HYD, etc.), like a terminal populating.
- The Airfare Index detail page: the methodology ribbon ("WEIGHTED MODIFIED LASPEYRES") and the advance-window breakdown (T+1 → T+45) revealing in sequence.

## Outro / punchline
Cut to black. Line types out: `Nothing on this dashboard is fake.` Beat. Second line: `Every number comes from the pipeline.` Logo/wordmark: "India Airfare Index" with the plane icon.

## User flow worth showing
Trigger a scrape → scrape run appears in "Recent Scrape Runs" as RUNNING → flips to SUCCESS with quotes ingested count → Latest Fare Quotes table updates with new rows → Airfare Index ticks to reflect it. Entry → key action (scrape completes) → result (index updates live).

## Tone
- Preset: polished
- Creative direction: national data-surveillance command terminal — restrained, serious, institutional
- Interpretation: Confident through restraint. Few scenes, longer holds, hard cuts instead of flashy transitions. Monospace typography does the talking. No jokes, no winking at the camera — the seriousness itself is the hook.

## Format: landscape — 1920x1080
## Duration: 20s

## Visual identity (from the project)
- Background: #f7f9fd (light dashboard bg), #0f172a (navy sidebar/terminal bg)
- Accent: #103aa5 (blue), #07583e (green, success states), #63e6be (live pulse dot)
- Text: #102238 (ink), #cbd5e1 (sidebar text), #94a3b8 (muted mono labels)
- Display font: IBM Plex Sans
- Body/mono font: JetBrains Mono
- Strongest visual element: the navy sidebar with pulsing live-status dot + monospace telemetry bar ("SOVEREIGN PIPELINE: ACTIVE SURVEILLANCE")

## Share copy (draft)
We built a live CPI for Indian flight prices — real Google Flights scrapes, a real cleaning pipeline, real index math. No hardcoded numbers, just a dashboard that doesn't lie.

## Audio direction
- Role: sparse professional accents over a restrained music bed
- Music: happy-beats-business-moves-vol-12-by-ende-dot-app.mp3 (117s, 109.96 BPM, "steady and clean" — best match for polished/cinematic per audio.md) — trimmed to 20s, used at low-mid volume
- Music treatment: starts near-silent under the hook typing, rises to ~0.3 volume on the dashboard reveal, holds steady through the data scenes, quick fade over the final 1.5s
- Music cue guidance: bundled preset at 109.96 BPM. Strong cues in range: 8.74s, 17.47s, 18.56s, 22.93s/24.56s (beyond 20s, ignore). Lock the Scene 2→3 data-reveal moment near 8.74s (±0.15s) and the Scene 3→4 transition near 17.47s (±0.15s) — both already align closely with the planned scene boundaries. Treat all other beats as loose backbone only, never for sequential text reveals.
- Audio-reactive treatment: none — keep visuals deterministic and calm, matching the polished/institutional tone
- SFX posture: sparse (2-3 total per audio.md polished guidance); a randomized single dry `keyboard/keypress-*.wav` per typed character on the hook and outro lines, one soft `interface/drop_001.ogg` on the scrape-run SUCCESS flip, one `interface/bong_001.ogg` as a restrained accent on the final logo landing
- Audio-coupled moments: the hook typing (keypress sfx, randomized per character), the scrape run flipping to SUCCESS (drop_001), the outro lines typing (keypress sfx), the logo landing (bong_001, quiet)
- Restraint rule: no whooshes, no chaotic risers, no music swelling to fill silence, no more than 3 distinct SFX families — the silence itself should feel intentional and confident

## Storyboard

### Scene 1 — The hook — 3s
Black frame. Monospace text types in character by character: `SOVEREIGN PIPELINE: ACTIVE SURVEILLANCE`. Small live-pulse dot appears next to it after the line completes.
Sequential/interaction: yes — text types out character by character with a blinking cursor
Audio intent: tense, quiet anticipation — near silence except keystrokes
Audio-coupled idea: subtle keyboard-tick sfx synced to each character
Music: near-silent bed starting under this scene
Transition mood: hard cut → Scene 2

### Scene 2 — Dashboard reveal — 4s
Hard cut to the full Overview dashboard. Navy sidebar slides in from the left with nav items and the "MoSPI / GoI CPI Baseline" badge. Hero card ("Airfare Price Index") and KPI grid fade/slide in.
Sequential/interaction: yes — sidebar slides in first, then the 5 KPI cards arrive one by one left to right
Audio intent: confident arrival, music lifts slightly
Audio-coupled idea: soft card-arrive tick per KPI card
Music: bed rises to moderate volume here
Transition mood: clean wipe → Scene 3

### Scene 3 — Live data populating — 5s
Latest Fare Quotes table. Rows land one by one: corridor code, airline, fare, advance window — each row settling with a brief highlight. "Current Airfare Index" number ticks upward to its final value.
Sequential/interaction: yes — table rows arrive top to bottom, ~0.5-0.6s apart; index number count-up
Audio intent: mechanical precision, data feels alive
Audio-coupled idea: soft row-arrive tick per row, subtle tick-up sound on the counting number
Music: steady mid-volume bed, loosely following the beat grid for the row reveals
Transition mood: clean wipe → Scene 4

### Scene 4 — Methodology + scrape flow — 5s
Cut to the Airfare Index detail page: methodology ribbon "WEIGHTED MODIFIED LASPEYRES" holds on screen. Then a quick beat showing a scrape run flipping from RUNNING to SUCCESS with a quotes-ingested count, implying the live pipeline behind the numbers.
Sequential/interaction: yes — simulate the scrape-run status flipping (RUNNING → SUCCESS badge change)
Audio intent: quiet confirmation, a single clear payoff tick
Audio-coupled idea: one soft confirm tick on the SUCCESS flip
Music: bed holds steady, slight pull-back to leave room for the tick
Transition mood: dramatic wipe to black → Scene 5

### Scene 5 — Outro / punchline — 3s
Black frame. Line types: `Nothing on this dashboard is fake.` Beat (0.6s hold). Second line types below it: `Every number comes from the pipeline.` Logo mark fades in: plane icon + "India Airfare Index" wordmark.
Sequential/interaction: yes — two lines type in sequence with a hold between them, then logo fades in
Audio intent: calm, certain, final
Audio-coupled idea: keyboard-tick sfx on both typed lines, matching Scene 1
Music: fades out over the final 1.5s
Transition mood: — (end)

**Music mood for this video:** polished / restrained corporate-serious, used as a background bed rather than a driving force
**Audio summary:** Near-silent open, a confident but understated rise through the dashboard and data scenes, one clean payoff tick at the pipeline confirmation, then a calm fade to black — audio supports the "this is real infrastructure" claim without ever selling it too hard.
