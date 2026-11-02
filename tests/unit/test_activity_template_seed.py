"""The seeded standard templates must be valid templates.

seed_activity_template.sql inserts rows directly, bypassing Pydantic. If one of
them breaks a rule in activity_rules.py, nothing fails at seed time - the
supervisor only finds out when they open the template and cannot save it.

These tests mirror the seeded values and run them through the real schema, so a
seed row that would be unsaveable fails here instead.

Keep this in step with the SQL file. A mismatch means one of the two is wrong.
"""
from datetime import date

import pytest

from app.schemas.activity_template_schema import ActivityTemplateCreate

# Mirrors app/sql/activity_template/seed_activity_template.sql
SEEDED_TEMPLATES = [
    {
        "name": "Compulsory daily care",
        "title": "Daily care activity",
        "description": "A care task every patient attends at a fixed time each weekday.",
        "is_compulsory": True,
        "is_fixed": True,
        "is_group": False,
        "min_duration": 60,
        "max_duration": 60,
        "min_people_req": 1,
        "fixed_time_slots": "Monday 10:00,Tuesday 10:00,Wednesday 10:00,Thursday 10:00,Friday 10:00",
    },
    {
        "name": "Group session",
        "title": "Group activity",
        "description": "A shared activity run for a small group of patients.",
        "is_compulsory": False,
        "is_fixed": False,
        "is_group": True,
        "min_duration": 60,
        "max_duration": 60,
        "min_people_req": 4,
        "fixed_time_slots": None,
    },
    {
        "name": "Quiet individual activity",
        "title": "Quiet activity",
        "description": "A short solo activity, useful for filling gaps in a schedule.",
        "is_compulsory": False,
        "is_fixed": False,
        "is_group": False,
        "min_duration": 30,
        "max_duration": 30,
        "min_people_req": 1,
        "fixed_time_slots": None,
    },
    {
        "name": "Individual session",
        "title": "Individual activity",
        "description": "A one-to-one session, applied once per time slot it runs at.",
        "is_compulsory": False,
        "is_fixed": False,
        "is_group": False,
        "min_duration": 60,
        "max_duration": 60,
        "min_people_req": 1,
        "fixed_time_slots": None,
    },
]


@pytest.mark.parametrize("seeded", SEEDED_TEMPLATES, ids=lambda s: s["name"])
def test_seeded_template_is_valid(seeded):
    """Every seeded row passes the shared activity rules."""
    template = ActivityTemplateCreate(
        **seeded,
        start_date=date.today(),
        end_date=date(2999, 1, 1),
        created_by_id="1",
    )
    assert template.name == seeded["name"]


def test_seeded_names_are_unique():
    """The CRUD rejects a duplicate template name, so the seed cannot contain one."""
    names = [s["name"] for s in SEEDED_TEMPLATES]
    assert len(names) == len(set(names))


def test_compulsory_seed_carries_time_slots():
    """Compulsory implies fixed, and fixed requires slots.

    The one seeded template that is compulsory is also the only one that needs
    slots - worth asserting directly, because a well-meaning edit setting the
    others compulsory would break them.
    """
    compulsory = [s for s in SEEDED_TEMPLATES if s["is_compulsory"]]
    assert len(compulsory) == 1
    for s in compulsory:
        assert s["is_fixed"] is True
        assert s["fixed_time_slots"]


def test_no_seeded_template_is_fixed_without_slots():
    for s in SEEDED_TEMPLATES:
        if s["is_fixed"]:
            assert s["fixed_time_slots"], f"{s['name']} is fixed but has no slots"
