"""The shared activity-configuration rules.

test_centre_activity.py already covers these rules as reached through the Centre
Activity schema. These tests cover them as reached through a plain object, which
is how the Activity Template schema will use them - and which is the reason the
rules were extracted in the first place.
"""
from datetime import date
from types import SimpleNamespace

import pytest

from app.schemas.activity_rules import ALLOWED_DURATIONS, validate_activity_configuration


def config(**overrides):
    """A valid configuration, with overrides applied.

    Deliberately a SimpleNamespace rather than a Pydantic model: if these rules
    ever stop working on a plain object, the template schema can no longer share
    them and the extraction has been undone.
    """
    base = dict(
        is_compulsory=True,
        is_fixed=True,
        is_group=False,
        fixed_time_slots="Monday 11:00,Tuesday 11:00",
        start_date=date.today(),
        end_date=date(2999, 1, 1),
        min_duration=60,
        max_duration=60,
        min_people_req=1,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_valid_configuration_passes():
    validate_activity_configuration(config())


@pytest.mark.parametrize(
    "overrides, expected",
    [
        ({"is_group": True, "min_people_req": 1}, "Group activities must have a minimum of 2"),
        ({"is_group": False, "min_people_req": 2}, "Individual activities must have a minimum of 1 person"),
        ({"min_duration": 30, "max_duration": 60}, "same minimum and maximum duration"),
        ({"min_duration": 45, "max_duration": 45}, "Duration must be either 30 or 60 minutes."),
        ({"is_compulsory": True, "is_fixed": False}, "Compulsory activities must be fixed."),
        ({"is_compulsory": True, "is_fixed": True, "fixed_time_slots": "   "}, "Compulsory activities must have fixed time slots"),
        ({"is_compulsory": False, "is_fixed": True, "fixed_time_slots": None}, "Fixed activities must have fixed time slots"),
        ({"end_date": date(2000, 1, 1)}, "End date cannot be before start date."),
        ({"fixed_time_slots": "Monday11:00"}, "is not in the correct format"),
    ],
)
def test_invalid_configurations_raise(overrides, expected):
    with pytest.raises(ValueError) as exc:
        validate_activity_configuration(config(**overrides))
    assert expected in str(exc.value)


@pytest.mark.parametrize("duration", ALLOWED_DURATIONS)
def test_allowed_durations_pass(duration):
    """30 and 60 are the only durations the Scheduler can place, and the constant
    is shared so the template and centre activity schemas cannot disagree."""
    validate_activity_configuration(config(min_duration=duration, max_duration=duration))


def test_rules_do_not_read_fields_a_template_lacks():
    """A template has no activity_id, care_centre_id or id - it is a blank form.

    If a rule started reading one of those, the template schema could not reuse
    these rules, so this asserts the function never touches them.
    """
    validate_activity_configuration(config())  # config() defines none of those fields
