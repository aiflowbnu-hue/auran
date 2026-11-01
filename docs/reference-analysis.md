# Reference Video Analysis — "Yellow Dude" style gym explainers

Two reference videos analysed (frames every 2.5 s, motion samples at 6 fps, scene-cut detection,
loudness analysis, and word-level transcript with audio-event tags via ai33 / ElevenLabs STT).

| | Video A — "Get 6-pack abs faster with this simple morning routine" | Video B — "Why your tendons never heal" |
|---|---|---|
| Length | 5:05 | 5:30 |
| Format | 1280×720, 16:9, 25 fps | 1280×720, 16:9, 30 fps |
| Type | Workout tutorial (3 moves) | Science explainer + rehab advice |
| Voiceover | ~660 words, ~130 wpm | ~827 words, ~150 wpm |
| Sponsor | Saily eSIM (mid-roll 1:23–2:39 + outro) | Own product: "Calisthenics Playbook" (4:15–4:50) |
| Loudness | −27 LUFS integrated (quiet master) | −17 LUFS integrated (standard YouTube level) |

---

## 1. Visual style

- **100% 2D.** No 3D modelling anywhere. Hand-drawn vector illustration: thick black outlines,
  flat fills, one or two cel-shade tones for muscle definition.
- **Mascot:** a faceless, muscular yellow man ("Yellow Dude"): only two white eye shapes,
  grey shorts, grey arm sleeve on one arm, dark wristbands. He plays every role (doctor = same
  character + glasses + lab coat).
- **Backgrounds:** a single flat colour, no environment unless the joke needs it.
  - A: soft lavender-blue `#CFDBF5`-ish
  - B: light steel-blue `#C9D9E8`-ish, with darker blue `#3D5A80` for dramatic moments
- **Title cards:** dark slate `#4A5872` full-frame, white italic text: `#1` / `CRUCIFIX CRUNCH`.
- **Anatomy inserts:** semi-realistic muscle illustrations (red muscle, cream tendon/bone)
  shown inside **circular zoom bubbles** connected to the body with a line.

## 2. Animation level

- **Limited animation (pose-to-pose).** Most shots have 2–4 drawings swapped or tweened
  (e.g. snooze scene: the arm just alternates up/down with impact lines).
- Exercise demos = a few key poses with smooth in-betweens (rig/puppet-style, like
  After Effects Duik / Moho bones), plus small "breathing" idle motion.
- Life is added through **camera moves and effects**, not frame-by-frame drawing:
  slow push-ins, whip-pans with heavy motion blur, scale-pop-ins with overshoot,
  screen shake on impacts, glow/flash bursts, radial "sunburst" backgrounds for hype moments.
- **Very few hard cuts** (18 in A, 12 in B over 5 minutes). Instead, the frame is redressed
  continuously: elements fly in/out, zoom into a detail, zoom back out.

## 3. Editing & pacing

- A new visual idea every **2–3 seconds**, locked tightly to the voiceover: each sentence = one
  visual gag or illustration.
- Visual jokes literalise the script ("snooze button hits harder than your motivation" → fist
  smashing a giant SNOOZE button; "starfish that means business"; "WASTED" GTA screen after
  falling off Taipei 101).
- Repeated running gag: **banana** ("banana strong") pops up with a glow burst.
- Section rhythm: title card → demo → zoom-in on target muscle → form mistake (red ❌) →
  sets/reps text → joke.

## 4. Text & graphics

- One clean geometric sans (similar to **Jost / Futura**), mostly *italic*, black or dark slate.
- Minimal on-screen text: exercise names, `3 Sets` / `10 - 15 reps`, `30 - 45 sec`, single
  words animating in (`Suffering` → struck through in red → `Training`).
- Info-graphics: digital countdown timer (`00:09:03`), bar chart (B, "10 mins" study),
  weekly calendar grid, 3-step timeline bar (30 s / no rest / 30 s), staircase of progressions.
- Icons/overlays: red arrows, red ❌, 🔥 emoji, sweat drops, sparkles, Zzz, ghost leaving body,
  "?" thought bubbles.
- Persistent small "SPONSORED BY Saily" bug in the bottom-left during the sponsor segment.

## 5. Script structure

**Video A (tutorial)**
1. 0:00 Hook: relatable failure (snooze) → "Sound familiar? Here's your fix."
2. 0:11 Promise: 3 moves, no gear, 10 minutes, hits upper/lower/obliques.
3. 0:39 Catch-phrase "Banana strong? Let's go."
4. 0:42 Move #1: Crucifix crunch: how-to, form cue, mistake, sets/reps, joke.
5. 1:23 **Sponsor segue built from the content** (training in a hotel → bad Wi-Fi → roaming → Saily).
6. 2:39 "Back to suffering… I mean, training."
7. 2:45 Move #2: Core hold series (3 holds × 30 s, no rest).
8. 3:34 Move #3: Side plank raises.
9. 4:17 Recap: "3 moves, 1 round, under 10 minutes": 7-day challenge promise.
10. 4:33 Sponsor reminder → comment / tag a friend / subscribe → sign-off "Yellow Dude out."

**Video B (explainer)**
1. 0:00 Hook: quote a gym-bro myth ("heal in 36 hours"). Then "Let me explain."
2. 0:23 Definitions (ligament / fascia / tendon) with three anatomy circles.
3. 0:59 Zoom-inside journey (bundles inside bundles, "like Inception").
4. 1:28 Injury mechanism (fibers scatter), then spring analogy (jump/squat).
5. 2:14 Study/data (10-minute loading chart) → absurd example (free-solo Taipei 101 → WASTED).
6. 2:47 Doctor scene: tendonitis vs tendinopathy.
7. 3:13 Healing timeline (4–6 days vs 6 months).
8. 3:40 Solution: eccentric exercises (spotlight title).
9. 4:15 Product pitch (Calisthenics Playbook) tied to the problem ("you skipped progressions").
10. 4:48 Wrap-up joke (AI doctor) → closing message → end screen.

**Tone:** second-person ("you"), sarcastic gym-bro humour, a joke every 2–3 sentences, short punchy
lines, clear science underneath.

## 6. Audio

- **Voiceover:** single male English narrator, casual and confident, a little deadpan. Almost
  wall-to-wall (only ~5.6 s total silence in A, ~3.3 s in B).
- **Music:** a quiet bed under the voice (measured noise floor between words ≈ −50 dB), louder
  during the exercise-hold section of A (3:00–4:00, floor ≈ −36 dB); an upbeat music sting at
  the end of both videos (tagged by STT at 4:57 in A and 5:20 in B).
- **SFX (inferred from visuals, not heard):** whooshes on whip-pans, pops on element pop-ins,
  impact/punch on snooze smash, ding/sparkle on glow bursts, record-scratch/fail sting on
  "WASTED", fire crackle on 🔥, clock tick on timers. These are typical for the style; exact
  sounds must be confirmed by ear.

## 7. How to recreate (production plan)

| Layer | Tool / method |
|---|---|
| Script | Same 10-beat structure, new topic and new jokes |
| Voiceover | ai33 Text-to-Speech (male, casual narrator voice) |
| SFX | ai33 Sound Effect (whoosh, pop, punch, ding, tick, fail sting) |
| Music | ai33 Music (light upbeat lo-fi/funk bed + end sting) |
| Character & art | Our own original mascot (different design from Yellow Dude), flat 2D vector SVG |
| Animation | Code-driven 2D (SVG/canvas → rendered frame by frame → ffmpeg MP4): pose swaps, tweens, camera zooms, motion blur, pop-ins |
| Edit/mix | ffmpeg: VO + ducked music + SFX at visual cue times, loudness normalised to −14 LUFS |

Note: the new video must use **our own character, colours and jokes**. Copy the *format and
pacing*, not Yellow Dude's mascot or exact scenes.
