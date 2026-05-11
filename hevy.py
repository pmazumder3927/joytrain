#!/usr/bin/env python3
"""Minimal Hevy CLI for programming workouts from YAML files.

Workflow:
  ./hevy.py sync-exercises          # one-time cache of exercise templates
  ./hevy.py search "back squat"     # fuzzy lookup
  ./hevy.py push workouts/<file>.yaml [--update]  # push as Hevy routine
  ./hevy.py folders                 # list routine folders
  ./hevy.py routines                # list routines
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
import time
from pathlib import Path

import requests
import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
CACHE_DIR = ROOT / ".hevy_cache"
EXERCISES_CACHE = CACHE_DIR / "exercises.json"
ROUTINES_CACHE = CACHE_DIR / "routines.json"
PUSHED_INDEX = CACHE_DIR / "pushed.json"
BASE_URL = "https://api.hevyapp.com/v1"
LB_TO_KG = 0.45359237


def api_key() -> str:
    load_dotenv(ROOT / ".env")
    key = os.environ.get("HEVY_API_KEY")
    if not key:
        sys.exit("HEVY_API_KEY not set. Put it in .env or export it.")
    return key


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"api-key": api_key(), "accept": "application/json"})
    return s


def paginate(s: requests.Session, path: str, page_size: int = 100, key: str | None = None):
    page = 1
    while True:
        r = s.get(f"{BASE_URL}{path}", params={"page": page, "pageSize": page_size})
        r.raise_for_status()
        data = r.json()
        if key is None:
            key = next((k for k in data if isinstance(data[k], list)), None)
        items = data.get(key, [])
        yield from items
        if page >= data.get("page_count", 1) or not items:
            return
        page += 1


def cmd_sync_exercises(_args):
    CACHE_DIR.mkdir(exist_ok=True)
    s = session()
    items = list(paginate(s, "/exercise_templates", page_size=100, key="exercise_templates"))
    EXERCISES_CACHE.write_text(json.dumps(items, indent=2))
    print(f"cached {len(items)} exercise templates → {EXERCISES_CACHE}")


def load_exercises() -> list[dict]:
    if not EXERCISES_CACHE.exists():
        sys.exit("no exercise cache. run: ./hevy.py sync-exercises")
    return json.loads(EXERCISES_CACHE.read_text())


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def resolve_exercise(name: str, exercises: list[dict]) -> dict:
    """Resolve a name (or explicit id) to an exercise template, with strict fuzzy match."""
    # Direct id match
    for ex in exercises:
        if ex["id"] == name:
            return ex
    target = _norm(name)
    # Exact normalized title match
    exact = [ex for ex in exercises if _norm(ex["title"]) == target]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        sys.exit(f"ambiguous exact match for {name!r}: {[e['title'] for e in exact]}")
    # Substring match
    sub = [ex for ex in exercises if target in _norm(ex["title"])]
    if len(sub) == 1:
        return sub[0]
    # Fuzzy match
    titles = [ex["title"] for ex in exercises]
    close = difflib.get_close_matches(name, titles, n=5, cutoff=0.6)
    if len(sub) > 1:
        sys.exit(
            f"ambiguous exercise {name!r}. candidates:\n  - "
            + "\n  - ".join(e["title"] for e in sub[:10])
        )
    sys.exit(
        f"no exercise match for {name!r}. closest:\n  - " + "\n  - ".join(close)
        if close
        else f"no exercise match for {name!r}"
    )


def cmd_search(args):
    exs = load_exercises()
    q = _norm(args.query)
    hits = [e for e in exs if q in _norm(e["title"])]
    hits.sort(key=lambda e: (not e["title"].lower().startswith(args.query.lower()), e["title"]))
    if not hits:
        # fall back to fuzzy
        titles = [e["title"] for e in exs]
        for t in difflib.get_close_matches(args.query, titles, n=10, cutoff=0.5):
            ex = next(e for e in exs if e["title"] == t)
            print(f"{ex['id']}  {ex['title']}  ({ex['primary_muscle_group']})")
        return
    for ex in hits[:20]:
        print(f"{ex['id']}  {ex['title']}  ({ex['primary_muscle_group']})")


# ── YAML → API payload ─────────────────────────────────────────────────────────

ALLOWED_RPE = {6, 7, 7.5, 8, 8.5, 9, 9.5, 10}


def _weight_kg(raw: dict) -> float | None:
    if "weight_kg" in raw and raw["weight_kg"] is not None:
        return float(raw["weight_kg"])
    if "weight_lb" in raw and raw["weight_lb"] is not None:
        return round(float(raw["weight_lb"]) * LB_TO_KG, 2)
    return None


def _expand_sets(raw_sets: list[dict]) -> list[dict]:
    """Expand `count: N` shorthand. Returns list of normalized set dicts."""
    out = []
    for s in raw_sets:
        count = int(s.pop("count", 1))
        for _ in range(count):
            out.append(dict(s))
    return out


def _build_set(s: dict) -> dict:
    """Build a routine set payload. Hevy rejects `rpe` on routine sets
    (it's only logged during a workout) so we strip it here — the caller
    is responsible for folding per-set RPE prescription into exercise notes."""
    rpe = s.get("rpe")
    if rpe is not None and float(rpe) not in ALLOWED_RPE:
        sys.exit(f"RPE must be one of {sorted(ALLOWED_RPE)}, got {rpe}")
    payload = {
        "type": s.get("type", "normal"),
        "weight_kg": _weight_kg(s),
        "reps": s.get("reps"),
        "distance_meters": s.get("distance_meters"),
        "duration_seconds": s.get("duration_seconds"),
        "custom_metric": s.get("custom_metric"),
    }
    rng = s.get("rep_range")
    if rng:
        payload["rep_range"] = {"start": rng[0], "end": rng[1]} if isinstance(rng, (list, tuple)) else rng
    return payload


def _format_set_prescription(sets: list[dict]) -> str:
    """Build a short, human-readable per-set summary including RPE — fed
    into the exercise notes since Hevy strips RPE from routine sets."""
    parts = []
    i = 1
    while i <= len(sets):
        s = sets[i - 1]
        # Group consecutive identical sets
        run = 1
        while i + run <= len(sets) and sets[i + run - 1] == s:
            run += 1
        bits = []
        if s.get("reps") is not None:
            bits.append(f"{s['reps']} reps")
        if s.get("duration_seconds") is not None:
            bits.append(f"{s['duration_seconds']}s")
        if s.get("distance_meters") is not None:
            bits.append(f"{s['distance_meters']}m")
        w = _weight_kg(s)
        if w is not None:
            lb = round(w / LB_TO_KG)
            bits.append(f"@ {lb} lb")
        if s.get("rpe") is not None:
            bits.append(f"RPE {s['rpe']}")
        if not bits:
            i += run
            continue
        label = f"Set {i}" if run == 1 else f"Sets {i}-{i+run-1}"
        parts.append(f"{label}: {' '.join(bits)}")
        i += run
    return " · ".join(parts)


def build_routine_payload(spec: dict, exercises: list[dict]) -> tuple[dict, str | None]:
    """Returns (payload, folder_name_or_None). Caller resolves folder→id."""
    title = spec.get("title") or spec.get("name")
    if not title:
        sys.exit("workout YAML must have a top-level `title`")
    notes = spec.get("notes", "")

    # superset labels → integers
    superset_ids: dict = {}
    next_superset_id = 0

    out_exercises = []
    for ex in spec.get("exercises", []):
        name = ex.get("exercise") or ex.get("name")
        if not name:
            sys.exit(f"exercise entry missing `exercise`/`name`: {ex}")
        tmpl = resolve_exercise(name, exercises)

        ss_key = ex.get("superset")
        if ss_key is None:
            ss_id = None
        else:
            if ss_key not in superset_ids:
                superset_ids[ss_key] = next_superset_id
                next_superset_id += 1
            ss_id = superset_ids[ss_key]

        sets = _expand_sets(list(ex.get("sets", [])))

        # Hevy strips rpe/rep_range from routine notes display, so synthesize
        # a prescription line and prepend it to the exercise notes.
        prescription = _format_set_prescription(sets)
        user_notes = ex.get("notes") or ""
        if prescription and prescription not in user_notes:
            notes = f"{prescription}\n{user_notes}".strip() if user_notes else prescription
        else:
            notes = user_notes or None

        out_exercises.append(
            {
                "exercise_template_id": tmpl["id"],
                "superset_id": ss_id,
                "rest_seconds": ex.get("rest_seconds"),
                "notes": notes,
                "sets": [_build_set(s) for s in sets],
            }
        )

    payload = {
        "routine": {
            "title": title,
            "folder_id": None,  # filled in by caller
            "notes": notes,
            "exercises": out_exercises,
        }
    }
    return payload, spec.get("folder")


# ── routines / folders ────────────────────────────────────────────────────────


def list_folders(s: requests.Session) -> list[dict]:
    return list(paginate(s, "/routine_folders", page_size=10, key="routine_folders"))


def ensure_folder(s: requests.Session, name: str) -> int:
    for f in list_folders(s):
        if f["title"] == name:
            return f["id"]
    r = s.post(f"{BASE_URL}/routine_folders", json={"routine_folder": {"title": name}})
    r.raise_for_status()
    return r.json()["routine_folder"]["id"]


def _load_pushed_index() -> dict:
    if PUSHED_INDEX.exists():
        return json.loads(PUSHED_INDEX.read_text())
    return {}


def _save_pushed_index(idx: dict) -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    PUSHED_INDEX.write_text(json.dumps(idx, indent=2))


def cmd_push(args):
    yaml_path = Path(args.file)
    spec = yaml.safe_load(yaml_path.read_text())
    exercises = load_exercises()
    payload, folder_name = build_routine_payload(spec, exercises)

    s = session()
    if folder_name:
        payload["routine"]["folder_id"] = ensure_folder(s, folder_name)

    idx = _load_pushed_index()
    key = str(yaml_path.resolve())
    existing_id = idx.get(key)

    if args.update and existing_id:
        # PUT requires PutRoutinesRequestBody (no folder_id field)
        put_payload = {
            "routine": {
                "title": payload["routine"]["title"],
                "notes": payload["routine"]["notes"],
                "exercises": payload["routine"]["exercises"],
            }
        }
        r = s.put(f"{BASE_URL}/routines/{existing_id}", json=put_payload)
        r.raise_for_status()
        body = r.json()
        node = body.get("routine") if isinstance(body, dict) else body
        if isinstance(node, list):
            node = node[0] if node else None
        title = node.get("title") if isinstance(node, dict) else payload["routine"]["title"]
        print(f"updated routine {existing_id}: {title}")
    else:
        r = s.post(f"{BASE_URL}/routines", json=payload)
        r.raise_for_status()
        body = r.json()
        # Response: {"routine": [{...}]} (list with one entry)
        node = body.get("routine") if isinstance(body, dict) else body
        if isinstance(node, list):
            node = node[0] if node else None
        rid = node["id"] if node else None
        idx[key] = rid
        _save_pushed_index(idx)
        print(f"created routine {rid}: {node.get('title') if node else ''}")
    print("open Hevy on your phone/web to start the workout.")


def cmd_folders(_args):
    for f in list_folders(session()):
        print(f"{f['id']}\t{f['title']}")


def cmd_routines(args):
    s = session()
    items = list(paginate(s, "/routines", page_size=10, key="routines"))
    ROUTINES_CACHE.parent.mkdir(exist_ok=True)
    ROUTINES_CACHE.write_text(json.dumps(items, indent=2))
    for r in items[: args.limit]:
        print(f"{r['id']}\t{r.get('folder_id')}\t{r['title']}")


def cmd_whoami(_args):
    r = session().get(f"{BASE_URL}/user/info")
    r.raise_for_status()
    print(json.dumps(r.json(), indent=2))


def main():
    p = argparse.ArgumentParser(prog="hevy")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("sync-exercises").set_defaults(func=cmd_sync_exercises)

    sp = sub.add_parser("search")
    sp.add_argument("query")
    sp.set_defaults(func=cmd_search)

    sp = sub.add_parser("push")
    sp.add_argument("file")
    sp.add_argument("--update", action="store_true", help="update the existing routine instead of creating a new one")
    sp.set_defaults(func=cmd_push)

    sub.add_parser("folders").set_defaults(func=cmd_folders)

    sp = sub.add_parser("routines")
    sp.add_argument("--limit", type=int, default=20)
    sp.set_defaults(func=cmd_routines)

    sub.add_parser("whoami").set_defaults(func=cmd_whoami)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
