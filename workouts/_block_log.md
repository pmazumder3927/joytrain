# Block log

Running ledger for Claude across sessions. **Update after every push.**
This is the trail — read it before programming new days so you know
what was prescribed, what's next, and what assumptions are in play.

---

## Macrocycle 1 — started 2026-05-11

Per `context/training-history.md` "Best current program implication", the macrocycle is a
5-block, ~21–23 week reconstruction of the user's 2021–2022 TrainHeroic
arc.

| Block | Theme                    | Length    | Source(s) (from context/training-history.md)        | Planned dates                   |
| ----: | ------------------------ | --------- | -------------------------------- | ------------------------------- |
|     1 | Restart                  | 4 wk      | Block 9 (Jul 2022) + Block 3 GPP | 2026-05-11 → 2026-06-07         |
|     2 | Base strength            | 5 wk      | Block 1 (Apr–Jun 2021)           | 2026-06-08 → 2026-07-12         |
|     3 | Strength intensification | 4 wk      | Block 2 (Jun 2021)               | 2026-07-13 → 2026-08-09         |
|     4 | Heavy strength           | 5 wk      | Block 8 (Mar–Apr 2022)           | 2026-08-10 → 2026-09-13         |
|     5 | Hypertrophy / GPP reset  | 4 wk      | Block 3 (Jul 2021)               | 2026-09-14 → 2026-10-11         |

Dates after Block 1 are placeholders — recalibrate after each block based
on calendar / feedback / readiness.

---

## Block 1 — Restart (2026-05-11 → 2026-06-07)

**Why this block exists:** `context/training-history.md` explicitly calls Block 9 (Jul 2022)
the "best model for current restart" — it was an explicit Week 1 block
and already a modernized blend of all prior themes. Block 1 mirrors that
template, blended with Block 3 (Jul 2021 GPP) accessory/conditioning
flavor.

**Cadence:** 4 days/week.
Planned weekly rhythm: **Mon / Tue / Thu / Fri**.
(Block 9 was 5-day-numbered; we compress to 4 since this is a re-entry,
preserving the Pause Squat / Strict Press / Deadlift / Bench anchors.)

**Day split:**

| Day | Anchor                  | Theme                                     |
| --- | ----------------------- | ----------------------------------------- |
| D1  | Pause Squat             | Squat + lower + core                      |
| D2  | Strict Press            | Upper push + upper pull + arms            |
| D3  | Deadlift                | Hinge + posterior + power (slams/carries) |
| D4  | Bench Press             | Upper push (horizontal) + DB conditioning |

**RPE / progression model:**

- **W1 (5/11–5/17):** RPE 7 across — calibration week. No current 1RM
  data; loads in YAML are best-guesses derived from Block 8 W5 (2022)
  visible weights, discounted because training state in 2026 is unknown.
  Whatever weight produces RPE 7 today *is* the W1 reference.
- **W2 (5/18–5/24):** +5% on main lifts, target RPE 7.5.
- **W3 (5/25–5/31):** +5% again, target RPE 8.
- **W4 (6/1–6/7):** Deload — 3×5 @ RPE 6.5 OR a 3RM baseline test on D1
  if recovery is good; decide on 5/31 based on the prior week.

**Load assumptions (anchor numbers, working weight only):**

| Lift             | 2022 visible (Block 8) | W1 starting top set | Source        |
| ---------------- | ---------------------- | ------------------- | ------------- |
| Pause Back Squat | ~176 lb @ 3RPM         | 145 lb × 8 @ RPE 7.5 | discounted    |
| Strict Press     | ~95% top set ~135 lb*  | 75 lb × 5 @ RPE 7.5 | discounted    |
| Deadlift         | @ 78% top set          | 225 lb × 5 @ RPE 7  | conservative  |
| Bench Press      | 4×6 working            | 135 lb × 6 @ RPE 7  | conservative  |

\* Strict press 95% load not directly visible — derived from Block 8 W5D1
"Strict Press 4×3 @ 90,90,90,95%".

**Coaching themes to keep present every day:**

- Mobility-rich warmup (Block 9 / Block 3 hybrid).
- Unilateral lower-body work (Bulgarian split squat, walking lunge, lateral
  lunge, SLRDL — Block 1 and Block 9 both leaned hard on this).
- Core every day — Block 1 (2021) and Block 9 (2022) both did this.
- Shoulder health (Y raise, face pull, Cuban press) even on non-upper
  days — distinctively present across Block 1, Block 4, and Block 8.
- Loaded carries on D3 (Block 9 W1D5 had trap-bar farmer carry).
- A med-ball-slam / power finisher on D3 (Block 9 + Block 3 both used it).

---

## Programmed sessions

Mark `[x]` after pushing. Note unusual choices in the right column.

| Date       | Block.W.D | Title                                   | File                                                  | Notes                              |
| ---------- | --------- | --------------------------------------- | ----------------------------------------------------- | ---------------------------------- |
| 2026-05-11 | B1 W1 D1  | Pause Squat + Lower (Restart)           | `2026-05-11_block1-w1d1-squat.yaml`                   | calibration day; RPE 7 across; loads are guesses; created custom `Banded Plank Walkout` |

---

## Custom exercises created

When `context/training-history.md` names a movement that doesn't exist in Hevy's library,
add it via `hevy.py create-exercise` and reference it here. Use the ID
in YAML to avoid `ambiguous exact match` if duplicates exist.

| Title                  | ID                                     | Type      | Equipment        | Muscle      | Notes                          |
| ---------------------- | -------------------------------------- | --------- | ---------------- | ----------- | ------------------------------ |
| Banded Plank Walkout   | `ac957bda-e1fb-4d7c-958c-0ff0e4fe6a66` | reps_only | resistance_band  | abdominals  | Block 9 W1D2 warmup primitive  |

The Hevy API has no template DELETE endpoint, so any mistakenly-created
duplicates have to be removed manually from the Hevy app (custom
exercises). The CLI's response-parsing bug that caused the original
duplicate has been fixed in `hevy.py`.

## Future-Claude TODO

- After 2026-05-11 lands: ask user for RPE feedback before programming
  W1 D2 (Tue 2026-05-12). Use that to anchor W2 loads.
- W1 D2 should be **Strict Press + upper pull + arms**, per Block 9 W1D4.
- W1 D3 should be **Deadlift + posterior chain + slams/carries**, per
  Block 9 W1D5 (the 5,5,5,3,3,3 @ 65-78% pattern — but at lower %s for
  restart).
- W1 D4 should be **Bench + DB accessories**, drawing from Block 8 W5D2.
- When Block 1 ends, re-read context/training-history.md Block 1 (2021) for Block 2 (2026)
  template — 3-day frequency, 5×5 / 4×5 main work, big accessory volume.
