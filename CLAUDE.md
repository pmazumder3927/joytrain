# joytrain — programming pmazumder's Hevy workouts

This repo is a barebones harness for Claude to author daily training and push
it to the user's Hevy account.

## The workflow

User prompts something like:

> @context/training-history.md — feedback: hip felt cranky on Tuesday's deadlift. Program today.

You then:

1. Read the referenced context (training history, current block plan, feedback).
2. Write a workout YAML to `workouts/YYYY-MM-DD_<slug>.yaml`.
3. Push it: `.venv/bin/python hevy.py push workouts/<file>.yaml`.
4. Tell the user it's in Hevy and call out anything they should know
   (e.g. "scaled squat down 10 lb because of the hip", "deload week 4").

Iterate: edit the YAML, re-run with `--update` to mutate the existing routine
rather than creating a new one.

## Commands

```bash
.venv/bin/python hevy.py sync-exercises          # refresh exercise template cache
.venv/bin/python hevy.py search "<name>"         # find canonical Hevy exercise names
.venv/bin/python hevy.py push <file.yaml>        # create routine
.venv/bin/python hevy.py push <file.yaml> --update  # update existing routine for that file
.venv/bin/python hevy.py folders                 # list routine folders
.venv/bin/python hevy.py routines                # list user's routines
.venv/bin/python hevy.py whoami                  # sanity check API key
.venv/bin/python hevy.py create-exercise \       # add a missing exercise as a custom template
    --title "Banded Plank Walkout" \
    --type reps_only \
    --equipment resistance_band \
    --muscle abdominals \
    --other shoulders full_body
```

The pushed-routine index lives at `.hevy_cache/pushed.json` (keyed by absolute
YAML path) so `--update` mutates the right routine.

## Workout YAML format

```yaml
title: "Block 2 Week 1 Day 1 — Squat + Push Press"
folder: "Programmed by Claude"   # auto-created if missing
notes: |
  Block 2: strength intensification. Mid-back tightness still present;
  pause at bottom of squat, control eccentric on push press.

exercises:
  - exercise: "Squat (Barbell)"        # canonical Hevy name — verify with `search`
    rest_seconds: 180
    notes: "Pause 1s at bottom on rep 1 each set. Brace before unrack."
    sets:
      - { count: 2, reps: 5, weight_lb: 185, rpe: 7 }   # 2 identical sets
      - { count: 3, reps: 5, weight_lb: 195, rpe: 7.5 } # 3 identical sets

  - exercise: "Overhead Press (Barbell)"
    rest_seconds: 150
    sets:
      - { count: 4, reps: 8, weight_lb: 95 }

  - superset: A                        # shared label = supersetted in Hevy
    exercise: "Bulgarian Split Squat"
    rest_seconds: 60
    sets:
      - { count: 3, reps: 8, weight_lb: 30 }            # 30 lb in each hand
  - superset: A
    exercise: "Plank"
    sets:
      - { count: 3, duration_seconds: 45 }
```

### Set fields

- `reps`, `weight_lb` or `weight_kg`, `duration_seconds`, `distance_meters`,
  `custom_metric`, `rpe` (one of 6, 7, 7.5, 8, 8.5, 9, 9.5, 10), `rep_range`
  (list `[lo, hi]`), `type` (`normal`/`warmup`/`failure`/`dropset`,
  defaults to `normal`).
- `count: N` repeats the same set N times — use this instead of pasting
  identical sets manually.

### Adding missing exercises

If `context/training-history.md` (or any source) names a movement that doesn't exist in
Hevy's library, **create it as a custom template — do not silently
substitute a different exercise.** Use `create-exercise` (above), then
re-push the routine.

`type` enum: `weight_reps`, `reps_only`, `bodyweight_reps`,
`bodyweight_assisted_reps`, `duration`, `weight_duration`,
`distance_duration`, `short_distance_weight`.

`equipment` enum: `none`, `barbell`, `dumbbell`, `kettlebell`, `machine`,
`plate`, `resistance_band`, `suspension`, `other`.

`muscle` / `other` enum: `abdominals`, `shoulders`, `biceps`, `triceps`,
`forearms`, `quadriceps`, `hamstrings`, `calves`, `glutes`, `abductors`,
`adductors`, `lats`, `upper_back`, `traps`, `lower_back`, `chest`,
`cardio`, `neck`, `full_body`, `other`.

The API has no `DELETE /v1/exercise_templates/{id}` — to remove a
mistakenly-created custom exercise, delete it manually in the Hevy app.
There is also a hidden custom-exercise quota; the CLI surfaces a 403 if
hit.

### Important Hevy API quirks

- **`rpe` and `rep_range` are NOT stored on routine sets** (only on logged
  workouts). The CLI silently strips them from the API payload but
  auto-prepends a per-set prescription line to the exercise notes so the user
  still sees "Sets 1-2: 5 reps @ 185 lb RPE 7" in Hevy. Always write `rpe` in
  the YAML when you intend it — it'll surface in the notes.
- **Exercise names must match the cached Hevy template** (or use the
  `exercise_template_id` directly). The resolver does substring + fuzzy match
  and fails loudly on ambiguity. When unsure, run `./hevy.py search`.
- **Hevy stores weights in kg.** Prefer `weight_lb` in YAML; the CLI converts.

### Common exercise names (Hevy canonical)

The user's `context/training-history.md` uses lifter shorthand. Map to Hevy:

| user says           | Hevy canonical                       |
| ------------------- | ------------------------------------ |
| Back Squat          | Squat (Barbell)                      |
| Strict Press        | Overhead Press (Barbell)             |
| Bench Press         | Bench Press (Barbell)                |
| Deadlift            | Deadlift (Barbell)                   |
| Sumo Deadlift       | Sumo Deadlift (Barbell) — verify     |
| RDL                 | Romanian Deadlift (Barbell)          |
| Single Leg RDL      | Single Leg Romanian Deadlift (...)  |
| Bulgarian Split Squat | Bulgarian Split Squat              |
| Hip Thrust          | Hip Thrust (Barbell)                 |
| Pause Back Squat    | Pause Squat (Barbell)                |
| Push Press          | Push Press                           |

If unsure, `./hevy.py search "<term>"` and pick from the list.

## File layout

```
joytrain/
├── .env                 # HEVY_API_KEY (gitignored)
├── .gitignore
├── .hevy_cache/         # exercise + pushed-routine cache (gitignored)
├── .venv/               # python venv (gitignored)
├── CLAUDE.md            # this file
├── README.md
├── context/
│   └── training-history.md  # user's training history (long-form context)
├── hevy.py              # CLI
├── requirements.txt
└── workouts/
    ├── _block_log.md    # running trail of programmed sessions / macrocycle plan
    └── YYYY-MM-DD_<slug>.yaml
```

## Style notes when programming

- Per-set RPE targets are valuable — write them. They land in the exercise
  notes automatically.
- The user has 11+ years of strength history (see `context/training-history.md`). Use real loads
  derived from prior visible weights, not hypothetical %1RM unless they ask.
- Naming: `YYYY-MM-DD_<short-slug>.yaml` (e.g. `2026-05-12_lower-strength.yaml`).
- Folder convention: name the folder by the block (e.g. `"Block 1 — Base"`)
  so the user can navigate cycles in the Hevy app.
- Keep exercise notes short and prescriptive — cue, tempo, target. The per-set
  prescription string is auto-prepended.
