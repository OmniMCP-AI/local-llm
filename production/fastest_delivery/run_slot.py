"""Run one scheduled Asia/Shanghai editorial slot and retain its outcome."""

import argparse
from datetime import datetime
from hashlib import sha256
import os
from pathlib import Path
import re
from subprocess import TimeoutExpired
from zoneinfo import ZoneInfo

from fastest_editorial import COPY, EDITORIAL_TIMEZONE, _public_origin, generate_package
from fastest_editorial.__main__ import _record
from fastest_release import ReleaseError, ReleaseStore

from .approval import decode_sealed, instant, json_bytes, read_sealed, seal
from .slot_store import SlotStore, slot_reference


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


def _draft_path(draft_dir, scheduled, revision):
    if not re.fullmatch(r"[0-9a-f]{64}", revision):
        raise ValueError("invalid scheduler draft revision")
    return draft_dir / scheduled.date().isoformat() / f"{revision}.json"


def _check_draft(draft, run, scheduled):
    if (
        draft["schema_version"] != 1 or draft["editorial_date"] != scheduled.date().isoformat()
        or draft["editorial_timezone"] != EDITORIAL_TIMEZONE or draft["locale"] != run["locale"]
        or draft["outcome"] not in ("story", "no_story")
        or (draft["outcome"] == "story" and not draft["story"]["evidence_destination"].startswith(
            run["public_origin"] + "/releases/"
        ))
    ):
        raise ValueError("retained draft differs from the scheduler slot")


def _finish_attempt(save, run, error=None, *, reconciled=False):
    attempt = run["attempts"][-1]
    attempt["reconciled_at" if reconciled else "finished_at"] = datetime.now(TIMEZONE).isoformat()
    if error is None:
        draft = run.pop("pending_draft")
        run["draft_revision"] = draft["draft_revision"]
        if "draft_dir_sha256" in run:
            run["outcome"] = draft["outcome"]
        run.pop("error", None)
    else:
        run["error"] = attempt["error"] = error
    save(run)
    return error


def _attempt(args, scheduled, run, save):
    run["attempts"].append({"started_at": datetime.now(TIMEZONE).isoformat()})
    save(run)
    if "pending_draft" not in run:
        if not args.database_url:
            return _finish_attempt(save, run, "release database is not configured")
        try:
            run["pending_draft"] = generate_package(
                ReleaseStore(args.database_url), editorial_date=scheduled.date(),
                locale=args.locale, public_origin=run["public_origin"],
            )
        except TimeoutExpired:
            return _finish_attempt(save, run, "release database read timed out")
        except ReleaseError:
            return _finish_attempt(save, run, "release database read failed")
        except (AttributeError, KeyError, OSError, TypeError, ValueError):
            return _finish_attempt(save, run, "editorial draft generation failed")
        save(run)

    try:
        _record(args.draft_dir, run["pending_draft"])
    except (OSError, ValueError):
        return _finish_attempt(save, run, "editorial draft could not be retained")
    return _finish_attempt(save, run)


def _reconcile_interruption(draft_dir, scheduled, save, run):
    pending = run.get("pending_draft")
    if pending is not None:
        draft_path = _draft_path(draft_dir, scheduled, pending["draft_revision"])
        if draft_path.is_file():
            if read_sealed(draft_path, "draft_revision") != pending:
                raise ValueError("retained draft differs from the scheduler slot")
            _finish_attempt(save, run, reconciled=True)
            return
    last = run["attempts"][-1]
    run["error"] = last["error"] = "previous editorial attempt was interrupted"
    save(run)


def _pending(run):
    last = run["attempts"][-1]
    return "finished_at" not in last and "reconciled_at" not in last and "error" not in last


def _check_postgres_run(run, scheduled):
    attempts = run["attempts"]
    invalid = "invalid PostgreSQL scheduler slot record"
    if (
        run["schema_version"] != 1 or run["scheduled_at"] != scheduled.isoformat()
        or run["mode"] not in MODES or run["locale"] not in COPY
        or run["public_origin"] != _public_origin(run["public_origin"])
        or not re.fullmatch(r"[0-9a-f]{64}", run["draft_dir_sha256"])
        or not isinstance(attempts, list) or not 1 <= len(attempts) <= MAX_ATTEMPTS
    ):
        raise ValueError(invalid)
    for attempt in attempts:
        instant(attempt["started_at"])
    last = attempts[-1]
    if "draft_revision" in run:
        if (
            _pending(run) or "error" in run or "error" in last or "pending_draft" in run
            or run["outcome"] not in ("story", "no_story")
            or not re.fullmatch(r"[0-9a-f]{64}", run["draft_revision"])
        ):
            raise ValueError(invalid)
    elif "outcome" in run or (not _pending(run) and last.get("error") != run["error"]):
        raise ValueError(invalid)
    if "pending_draft" in run:
        draft = decode_sealed(json_bytes(run["pending_draft"]), "draft_revision", "PostgreSQL selected draft")
        _check_draft(draft, run, scheduled)


def _process_slot(args, scheduled, settings, run, save):
    if run is None:
        now = datetime.now(TIMEZONE)
        if args.mode == "live" and (scheduled > now or scheduled.date() != now.date()):
            raise ValueError("a new live slot must be due on today's Asia/Shanghai editorial date")
        run = {**settings, "schema_version": 1, "scheduled_at": scheduled.isoformat(), "attempts": []}
    else:
        if any(run[key] != value for key, value in settings.items()):
            raise ValueError("slot settings differ from the retained run")
        if "draft_revision" not in run and _pending(run):
            _reconcile_interruption(args.draft_dir, scheduled, save, run)
        if "draft_revision" in run:
            revision = run["draft_revision"]
            draft = read_sealed(_draft_path(args.draft_dir, scheduled, revision), "draft_revision")
            _check_draft(draft, run, scheduled)
            if draft["draft_revision"] != revision or draft["outcome"] != run.get("outcome", draft["outcome"]):
                raise ValueError("retained draft differs from the scheduler slot")
            return None

    if len(run["attempts"]) >= MAX_ATTEMPTS:
        return run["error"]
    return _attempt(args, scheduled, run, save)


def _draft_directory_digest(directory):
    return sha256(os.fsencode(directory.resolve())).hexdigest()


def _run_slot(args, scheduled):
    from fcntl import LOCK_EX, flock

    args.draft_dir = args.draft_dir.resolve()
    settings = {
        "mode": args.mode, "public_origin": _public_origin(args.public_origin), "locale": args.locale,
    }
    if args.slot_db_service is not None:
        store = SlotStore(args.slot_db_service)
        settings["draft_dir_sha256"] = _draft_directory_digest(args.draft_dir)
        path = _slot_path(args.draft_dir / ".slot-locks", scheduled)
        reference = slot_reference(scheduled.isoformat())
    else:
        store = None
        settings["draft_dir"] = str(args.draft_dir)
        path = _slot_path(args.run_dir.resolve(), scheduled)
        reference = path
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with path.with_suffix(".lock").open("a") as lock:
        flock(lock, LOCK_EX)
        if store is not None:
            run = store.read(scheduled.isoformat())
            if run is not None:
                _check_postgres_run(run, scheduled)
            return reference, _process_slot(args, scheduled, settings, run, store.save)
        run = _load(path) if path.exists() else None
        if run is not None:
            del run["run_id"]
        return reference, _process_slot(args, scheduled, settings, run, lambda run: _save(path, run))


def postgres_scheduled_runs(service, start, end, draft_dir):
    runs = []
    modes = set()
    draft_directory_digest = _draft_directory_digest(draft_dir)
    for run in SlotStore(service).between(start, end):
        scheduled = instant(run["scheduled_at"]).astimezone(TIMEZONE)
        _check_postgres_run(run, scheduled)
        if run["draft_dir_sha256"] != draft_directory_digest:
            raise ValueError("draft directory differs from the retained scheduler settings")
        modes.add(run["mode"])
        projected = {
            "scheduled_at": run["scheduled_at"], "reference": slot_reference(run["scheduled_at"]),
            "run_id": run["run_id"], "attempts": run["attempts"], "status": "pending",
        }
        if "draft_revision" in run:
            projected.update(status=run["outcome"], draft_revision=run["draft_revision"])
        elif not _pending(run):
            projected.update(status="failed", error=run["error"])
        runs.append(projected)
    if len(modes) > 1:
        raise ValueError("pilot scheduler records mix live and rehearsal slots")
    return runs, next(iter(modes), None)


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
    retention = parser.add_mutually_exclusive_group(required=True)
    retention.add_argument("--run-dir", type=Path)
    retention.add_argument("--slot-db-service", help="Private libpq service name for PostgreSQL slot history.")
    parser.add_argument("--locale", choices=COPY, default="en")
    args = parser.parse_args(argv)
    try:
        scheduled = instant(args.scheduled_at).astimezone(TIMEZONE)
        reference, error = _run_slot(args, scheduled)
        print(reference)
        if error is not None:
            parser.exit(1, f"{error}\n")
    except OSError as error:
        detail = error if args.slot_db_service is None else "could not access the local draft or slot lock"
        parser.exit(1, f"invalid scheduler slot: {detail}\n")
    except (AttributeError, ImportError, KeyError, TypeError, ValueError, OverflowError) as error:
        parser.exit(1, f"invalid scheduler slot: {error}\n")


if __name__ == "__main__":
    main()
