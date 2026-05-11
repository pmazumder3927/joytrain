# joytrain

a personal tool for me to talk to claude to program my blocks/workouts into hevy.

i tell claude what i want. it writes a workout yaml in `workouts/YYYY-MM-DD_<slug>.yaml`, pushes it to my hevy account through the api. i open hevy on my phone and do the workout — routine has sets, reps, loads, rest timers, cues, demo links.

## what's here

- `hevy.py` — cli for the hevy api. creates routines, searches exercises, creates custom exercise templates when hevy doesn't have one
- `context/training-history.md` — my reconstructed 2021–2022 training arc (9 blocks across ~16 months). reference for what's worked before
- `workouts/` — every programmed session as yaml, one file per day. `_block_log.md` is the running ledger so claude knows what was already programmed, why, and what's next
- `CLAUDE.md` — what claude reads when working in this repo
- `.hevy_cache/` — local cache of hevy's exercise library + index of pushed routines (keyed by yaml path so `--update` finds the right routine)

## the loop

i prompt something like `@context/training-history.md program today, hip felt cranky tuesday on deadlift`. claude:

1. reads the context (history + block log + recent files)
2. writes a workout yaml
3. pushes it via `hevy.py push`
4. tells me what's there + anything to flag (scaled the squat down 10 lb because of the hip, deload week, etc.)

to iterate: edit the yaml, run `hevy.py push <file> --update`. mutates the same routine in hevy instead of making a new one.

## commands

```bash
.venv/bin/python hevy.py whoami                          # sanity check api key
.venv/bin/python hevy.py sync-exercises                  # refresh local exercise cache
.venv/bin/python hevy.py search "<name>"                 # find canonical hevy exercise name
.venv/bin/python hevy.py push <file.yaml>                # create routine
.venv/bin/python hevy.py push <file.yaml> --update       # update existing routine
.venv/bin/python hevy.py folders                         # list routine folders
.venv/bin/python hevy.py routines                        # list my routines
.venv/bin/python hevy.py create-exercise --title "..." \
    --type ... --equipment ... --muscle ...              # add a custom exercise template
```

## yaml format

minimal example — full reference is in `CLAUDE.md`:

```yaml
title: "Block 1 W1D1 — Pause Squat + Lower"
folder: "Block 1 — Restart"
notes: |
  week 1, day 1. squat focus.
  cues: pause 1s at bottom every rep. brace before unrack.

exercises:
  - exercise: "Pause Squat (Barbell)"
    rest_seconds: 180
    notes: "1s pause every rep. top set rpe 7-7.5."
    sets:
      - { reps: 5, weight_lb: 95, type: warmup }
      - { count: 3, reps: 8, weight_lb: 145, rpe: 7.5 }   # 3 identical working sets

  - superset: A
    exercise: "Bulgarian Split Squat"
    sets:
      - { count: 3, reps: 8, weight_lb: 30 }
  - superset: A
    exercise: "Plank"
    sets:
      - { count: 3, duration_seconds: 45 }
```

shared `superset:` label = supersetted in hevy. `count: N` repeats identical sets. set `type:` can be `normal` / `warmup` / `failure` / `dropset`. weights in `weight_lb` or `weight_kg` (cli converts to kg for the api). rpe must be one of `6, 7, 7.5, 8, 8.5, 9, 9.5, 10` — no other values.

## setup

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
echo "HEVY_API_KEY=<your-key>" > .env
.venv/bin/python hevy.py sync-exercises
```

needs hevy pro. get the api key at https://hevy.com/settings?developer.

## why

manually punching in 4 weeks of programming with sets/reps/cues/rest/demos is annoying. i forget what i did 3 weeks ago. this way claude reads what's been programmed, picks up where it left off, and i edit a yaml in 30 seconds instead of clicking around the app.
