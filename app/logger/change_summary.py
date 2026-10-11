import re
from typing import Any, List, Optional

_IGNORED = {k.lower() for k in (
    "modified_date", "modified_by_id", "updated_at", "UpdatedDateTime",
    "ModifiedDate", "ModifiedById", "modifiedById", "modified_by",
)}


def _label(key: str) -> str:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", key.replace("_", " "))
    words = [w for w in spaced.split() if w]
    if len(words) > 1 and words[-1].lower() == "id":
        words = words[:-1]
    return " ".join(w[:1].upper() + w[1:] for w in words)


def with_change_summary(message: str, original: Optional[Any], updated: Optional[Any], limit: int = 3) -> str:
    if not isinstance(original, dict) or not isinstance(updated, dict):
        return message
    changed: List[str] = []
    for key in original:
        if key not in updated or key.lower() in _IGNORED:
            continue
        if original.get(key) != updated.get(key):
            changed.append(_label(key))
    if not changed:
        return message
    shown = changed[:limit]
    extra = len(changed) - len(shown)
    suffix = ", ".join(shown) + (f", +{extra} more" if extra else "")
    return f"{message} (changed: {suffix})"
