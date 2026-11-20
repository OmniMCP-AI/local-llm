"""Run one scheduled Asia/Shanghai editorial slot and retain its outcome."""

import argparse
from datetime import datetime
import os
from pathlib import Path
from subprocess import TimeoutExpired
from zoneinfo import ZoneInfo

from fastest_editorial import COPY, EDITORIAL_TIMEZONE, _public_origin, generate_package
from fastest_editorial.__main__ import _record
from fastest_release import ReleaseError, ReleaseStore

from .approval import instant, json_bytes, read_sealed, seal


TIMEZONE = ZoneInfo(EDITORIAL_TIMEZONE)
MODES = ("live", "rehearsal")
MAX_ATTEMPTS = 2


def _slot_path(directory, scheduled):
    return directory / scheduled.date().isoformat() / scheduled.strftime("%H%M%S.%f.json")


def _load(path):
    run = read_sealed(path, "run_id")
    scheduled = instant(run["scheduled_at"]).astimezone(TIMEZONE)
    if (
        run["schema_version"] != 1 or run["mode"] not in MODES
        or run["scheduled_at"] != scheduled.isoformat()
        or _slot_path(path.parent.parent, scheduled) != path
    ):
        raise ValueError(f"invalid scheduler slot record: {path}")
    return run


def _save(path, run):
    temporary = path.with_suffix(".tmp")
    try:
        with os.fdopen(os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "wb") as staged:
            staged.write(json_bytes(seal(run, "run_id")))
            staged.flush()
            os.fsync(staged.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _draft_path(run, revision):
    day = instant(run["scheduled_at"]).astimezone(TIMEZONE).date().isoformat()
    return Path(run["draft_dir"]) / day / f"{revision}.json"


def _finish_attempt(path, run, error=None, *, reconciled=False):
    attempt = run["attempts"][-1]
    attempt["reconciled_at" if reconciled else "finished_at"] = datetime.now(TIMEZONE).isoformat()
    if error is None:
        run["draft_revision"] = run.pop("pending_draft")["draft_revision"]
        run.pop("error", None)
    else:
        run["error"] = attempt["error"] = error
    _save(path, run)
    return error


def _attempt(args, scheduled, run, path):
    run["attempts"].append({"started_at": datetime.now(TIMEZONE).isoformat()})
    _save(path, run)
    if "pending_draft" not in run:
        if not args.database_url:
            return _finish_attempt(path, run, "release database is not configured")
        try:
            run["pending_draft"] = generate_package(
                ReleaseStore(args.database_url), editorial_date=scheduled.date(),
                locale=args.locale, public_origin=run["public_origin"],
            )
        except TimeoutExpired:
            return _finish_attempt(path, run, "release database read timed out")
        except ReleaseError:
            return _finish_attempt(path, run, "release database read failed")
        except (AttributeError, KeyError, OSError, TypeError, ValueError):
            return _finish_attempt(path, run, "editorial draft generation failed")
        _save(path, run)

    try:
        _record(args.draft_dir, run["pending_draft"])
    except (OSError, ValueError):
        return _finish_attempt(path, run, "editorial draft could not be retained")
    return _finish_attempt(path, run)


def _reconcile_interruption(path, run):
    pending = run.get("pending_draft")
    if pending is not None:
        draft_path = _draft_path(run, pending["draft_revision"])
        if draft_path.is_file():
            if read_sealed(draft_path, "draft_revision") != pending:
                raise ValueError("retained draft differs from the scheduler slot")
            _finish_attempt(path, run, reconciled=True)
            return
    last = run["attempts"][-1]
    run["error"] = last["error"] = "previous editorial attempt was interrupted"
    _save(path, run)


def _run_slot(args, scheduled):
    from fcntl import LOCK_EX, flock

    args.run_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = _slot_path(args.run_dir.resolve(), scheduled)
    path.parent.mkdir(mode=0o700, exist_ok=True)
    settings = {
        "mode": args.mode,
        "public_origin": _public_origin(args.public_origin),
        "locale": args.locale,
        "draft_dir": str(args.draft_dir.resolve()),
    }
    with path.with_suffix(".lock").open("a") as lock:
        flock(lock, LOCK_EX)
        if path.exists():
            run = _load(path)
            del run["run_id"]
            if any(run[key] != value for key, value in settings.items()):
                raise ValueError("slot settings differ from the retained run")
            last = run["attempts"][-1]
            if "draft_revision" not in run and "finished_at" not in last and "error" not in last:
                _reconcile_interruption(path, run)
            if "draft_revision" in run:
                revision = run["draft_revision"]
                draft = read_sealed(_draft_path(run, revision), "draft_revision")
                if draft["draft_revision"] != revision:
                    raise ValueError("retained draft differs from the scheduler slot")
                return path, None
        else:
            now = datetime.now(TIMEZONE)
            if args.mode == "live" and (scheduled > now or scheduled.date() != now.date()):
                raise ValueError("a new live slot must be due on today's Asia/Shanghai editorial date")
            run = {**settings, "schema_version": 1, "scheduled_at": scheduled.isoformat(), "attempts": []}

        if len(run["attempts"]) >= MAX_ATTEMPTS:
            return path, run["error"]
        return path, _attempt(args, scheduled, run, path)


def scheduled_runs(directory, days):
    runs = []
    modes = set()
    if directory is not None:
        for day in days:
            for path in sorted((directory / day).glob("*.json")):
                run = _load(path)
                modes.add(run["mode"])
                outcome = {key: run[key] for key in ("draft_revision", "error") if key in run}
                if outcome:
                    runs.append({
                        "scheduled_at": run["scheduled_at"], "reference": str(path.resolve()),
                        "attempts": run["attempts"], **outcome,
                    })
    if len(modes) > 1:
        raise ValueError("pilot scheduler records mix live and rehearsal slots")
    return runs, next(iter(modes), None)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.environ.get("FASTEST_EDITORIAL_DATABASE_URL"))
    parser.add_argument("--public-origin", required=True)
    parser.add_argument("--scheduled-at", required=True, help="Planned slot timestamp with a UTC offset.")
    parser.add_argument("--mode", required=True, choices=MODES)
    parser.add_argument("--draft-dir", type=Path, default=Path("editorial-drafts"))
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--locale", choices=COPY, default="en")
    args = parser.parse_args(argv)
    try:
        scheduled = instant(args.scheduled_at).astimezone(TIMEZONE)
        path, error = _run_slot(args, scheduled)
        print(path)
        if error is not None:
            parser.exit(1, f"{error}\n")
    except (ImportError, KeyError, OSError, TypeError, ValueError, OverflowError) as error:
        parser.exit(1, f"invalid scheduler slot: {error}\n")


if __name__ == "__main__":
    main()
