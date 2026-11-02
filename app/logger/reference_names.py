"""Adds human-readable activity / routine names next to their IDs in audit data."""
import logging
import time
from typing import Dict, List, Optional, Tuple

from sqlalchemy import text

CACHE_TTL_SECONDS = 300

_log = logging.getLogger(__name__)

# ID key -> (lookup kind, name key)
KEY_MAP = {
    "activity_id": ("activity", "activity_name"),
    "centre_activity_id": ("centre_activity", "centre_activity_name"),
    "old_centre_activity_id": ("centre_activity", "old_centre_activity_name"),
    "new_centre_activity_id": ("centre_activity", "new_centre_activity_name"),
    "routine_id": ("routine", "routine_name"),
}

_cache: Dict[Tuple[str, int], Tuple[float, Optional[str]]] = {}


def _fetch_names(kind: str, ids: List[int]) -> Dict[int, str]:
    """Look up names for ids (soft-deleted rows included) using a short own session."""
    from app.database import SessionLocal
    from app.models.activity_model import Activity
    from app.models.centre_activity_model import CentreActivity
    from app.models.routine_model import Routine

    db = SessionLocal()
    try:
        # Fail fast instead of waiting on rows locked by the in-flight request.
        db.execute(text("SET LOCK_TIMEOUT 500"))
        if kind == "activity":
            rows = db.query(Activity.id, Activity.title).filter(Activity.id.in_(ids)).all()
        elif kind == "centre_activity":
            rows = (
                db.query(CentreActivity.id, Activity.title)
                .join(Activity, Activity.id == CentreActivity.activity_id)
                .filter(CentreActivity.id.in_(ids))
                .all()
            )
        elif kind == "routine":
            rows = db.query(Routine.id, Routine.name).filter(Routine.id.in_(ids)).all()
        else:
            return {}
        return {r[0]: r[1] for r in rows if r[1] is not None}
    finally:
        # LOCK_TIMEOUT sticks to the pooled connection; restore the default.
        try:
            db.execute(text("SET LOCK_TIMEOUT -1"))
        except Exception:
            pass
        db.close()


def _resolve(wanted: Dict[str, set]) -> Dict[Tuple[str, int], str]:
    now = time.time()
    found: Dict[Tuple[str, int], str] = {}
    for kind, ids in wanted.items():
        missing = []
        for i in ids:
            hit = _cache.get((kind, i))
            if hit and now - hit[0] < CACHE_TTL_SECONDS:
                if hit[1] is not None:
                    found[(kind, i)] = hit[1]
            else:
                missing.append(i)
        if missing:
            names = _fetch_names(kind, missing)
            for i in missing:
                _cache[(kind, i)] = (now, names.get(i))
                if i in names:
                    found[(kind, i)] = names[i]
    return found


def add_reference_names(data):
    """Return a copy of data with *_name keys added beside known activity/routine IDs.

    Never raises; on any failure the data is returned unchanged.
    """
    if not isinstance(data, dict):
        return data
    try:
        wanted: Dict[str, set] = {}
        for key, (kind, name_key) in KEY_MAP.items():
            value = data.get(key)
            if isinstance(value, int) and not isinstance(value, bool) and name_key not in data:
                wanted.setdefault(kind, set()).add(value)
        if not wanted:
            return data
        found = _resolve(wanted)
        out = dict(data)
        for key, (kind, name_key) in KEY_MAP.items():
            value = data.get(key)
            if name_key not in out and (kind, value) in found:
                out[name_key] = found[(kind, value)]
        return out
    except Exception as exc:
        _log.warning("Could not resolve reference names: %s", exc)
        return data
