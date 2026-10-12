from app.logger.change_summary import with_change_summary


def test_lists_changed_fields_humanised():
    msg = with_change_summary("Updated Centre Activity: Gardening",
                              {"start_time": "10:00", "is_compulsory": False, "name": "G"},
                              {"start_time": "11:00", "is_compulsory": True, "name": "G"})
    assert msg == "Updated Centre Activity: Gardening (changed: Start Time, Is Compulsory)"


def test_limits_and_counts_extra_fields():
    before = {"a": 1, "b": 1, "c": 1, "d": 1, "e": 1}
    after = {"a": 2, "b": 2, "c": 2, "d": 2, "e": 2}
    assert with_change_summary("Updated X", before, after) == "Updated X (changed: A, B, C, +2 more)"


def test_ignores_bookkeeping_fields_and_leaves_message_alone():
    assert with_change_summary("Updated X", {"modified_date": "a", "ModifiedById": "u1"},
                               {"modified_date": "b", "ModifiedById": "u2"}) == "Updated X"


def test_non_dict_or_missing_sides_leave_message_alone():
    assert with_change_summary("Updated X", None, {"a": 1}) == "Updated X"
    assert with_change_summary("Updated X", "{}", {"a": 1}) == "Updated X"


def test_drops_trailing_id_in_labels():
    assert with_change_summary("Updated X", {"centre_activity_id": 1}, {"centre_activity_id": 2}) == \
        "Updated X (changed: Centre Activity)"


def test_ignores_keys_present_on_only_one_side():
    assert with_change_summary("Updated X", {"name": "A", "start_time": "10:00"},
                               {"start_time": "11:00", "extra_schema_field": 5}) == "Updated X (changed: Start Time)"


def test_no_overlapping_keys_leaves_message_alone():
    assert with_change_summary("Updated X", {"a": 1}, {"b": 2}) == "Updated X"
