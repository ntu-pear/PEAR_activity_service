"""Rules every activity configuration must satisfy, in one place.

These apply to a Centre Activity and to an Activity Template, because a template
is a blank activity form carrying the same fields. Keeping one definition means a
rule change lands once rather than twice - the duration rules in particular are
expected to relax so flexible activities can carry a genuine range, and two copies
would drift the moment that happens.

Duck-typed on purpose: anything exposing the field names below can be validated,
so the template schema does not have to inherit from the Centre Activity schema to
reuse the rules.
"""
from datetime import datetime

# The only durations the Scheduler can place. Kept here so the template schema
# and the Centre Activity schema cannot disagree about it.
ALLOWED_DURATIONS = (30, 60)


def validate_activity_configuration(data) -> None:
    """Raise ValueError on the first rule the configuration breaks.

    `data` is any object exposing is_compulsory, is_fixed, is_group,
    fixed_time_slots, start_date, end_date, min_duration, max_duration and
    min_people_req.
    """
    is_compulsory = data.is_compulsory
    is_fixed = data.is_fixed
    is_group = data.is_group
    fixed_time_slots = data.fixed_time_slots
    end_date = data.end_date
    min_duration = data.min_duration
    max_duration = data.max_duration
    min_people_req = data.min_people_req

    if is_group and (min_people_req is None or min_people_req < 2):
        raise ValueError("Group activities must have a minimum of 2 people required.")
    if not is_group and min_people_req != 1:
        raise ValueError("Individual activities must have a minimum of 1 person required.")
    if min_duration is None or max_duration is None or min_duration != max_duration:
        raise ValueError("Activities must have the same minimum and maximum duration.")
    # Planned: allow flexible activities a genuine range instead of a single value.
    # Relaxing the equality check above goes together with restoring this one, and
    # with the matching elif in centre_activity_availability_crud.
    # if not is_fixed and (min_duration is None or max_duration is None or min_duration > max_duration):
    #     raise ValueError("Flexible activities, ensure minimum duration is less than or equal to maximum duration.")
    if end_date and end_date < data.start_date:
        raise ValueError("End date cannot be before start date.")

    # Not in SRS, but Scheduler's limitation - compulsory activities must be fixed
    if is_compulsory and not is_fixed:
        raise ValueError("Compulsory activities must be fixed.")
    if is_compulsory and (fixed_time_slots is None or fixed_time_slots.strip() == ''):
        raise ValueError("Compulsory activities must have fixed time slots specified.")
    if is_fixed and (fixed_time_slots is None or fixed_time_slots.strip() == ''):
        raise ValueError("Fixed activities must have fixed time slots specified.")
    if (
        min_duration is None or min_duration not in ALLOWED_DURATIONS
        or max_duration is None or max_duration not in ALLOWED_DURATIONS
    ):
        raise ValueError("Duration must be either 30 or 60 minutes.")

    for slot in (fixed_time_slots.split(",") if fixed_time_slots else []):
        try:
            datetime.strptime(slot, "%A %H:%M")
        except ValueError:
            raise ValueError(
                f"Slot {slot} is not in the correct format. "
                "Expected format: 'Day HH:MM' (no space, separated by comma)."
            )
