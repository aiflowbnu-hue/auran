# Auran video projects

The owner talks in Roman Urdu/Hindi; reply the same way.

## Editing preferences for new image + voiceover projects (owner's standing instruction)

When the owner sends a voiceover plus a set of images to edit:

- **No zoom at all**: no zoom-in, no zoom-out, no push-in / Ken Burns, no zoom-punch.
- **No transitions**: plain hard cuts only (no bounce/pop, no shake, no whoosh-on-cut, no fades between images).
- **No sound effects.** Only the voiceover plus a quiet background music bed, unless the owner asks for SFX in that project.
- Still sync every cut to the spoken words (word-level speech-to-text via ai33, then snap each image to the start of its sentence).
- **Text overlays must be exactly on the voice, never late.** A frame that pops in text goes on the spoken word that the
  text shows (not on the guide's cue, which often belongs to the next phrase); the plain scene frame before it moves earlier
  if needed. Text frames appear ~0.3 s before their word; scene frames ~0.08 s before. Watch for numbers spoken as words ("40,000" = "forty
  thousand", "2:00" = "two", "100 MPH" = "hundred miles") and contractions ("you are"/"you're" vs "aren't").
  After rendering, verify no text frame appears after its word. See `projects/sentinel-hardcuts/build_edit.py`.
- Output 1920x1080, 30 fps, loudness about -14 LUFS.

The renderer in `projects/sentinel-hypothesis/` (`build_edit.py` + `render.js`) is the template; for new projects set every cut's
`fx` to `[]` and `sfx` to `[]`.

## Tools

- `tools/ai33.py`: ai33.pro client (sfx, tts, image). Needs the API key in the `AI33_KEY` environment variable; never commit it.
- Speech-to-text: `POST https://api.ai33.pro/v1/task/speech-to-text`, poll `GET /v1/task/{id}`, download `metadata.json_url`.
