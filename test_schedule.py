from schedule import (
    AttendeePreference,
    SessionOptions,
    Schedule,
    generate_all_chooses,
    generate_fixed_width_schedules,
    extract_attendee_preferences,
)

import pandas


def test_extract_attendee_preferences():
    """
    WHEN extracting attendee preferneces
    THEN a list of preferences will be returned
    """
    test_preferences = pandas.DataFrame(
        [
            [1, 2],
            [2, pandas.NA],
        ],
        columns=['Test topic 1', 'Test topic 2'],
        index=['t1', 't2'],
    )
    attendee_preferences = extract_attendee_preferences(test_preferences)
    assert all([isinstance(pref, AttendeePreference) for pref in attendee_preferences])
    assert attendee_preferences[0].attendee == 't1'
    assert attendee_preferences[0].preferences == {"Test topic 1": 1, "Test topic 2": 2}
    assert attendee_preferences[1].preferences == {"Test topic 1": 2}


def test_calculate_loss_for_attendee_choice():
    """
    WHEN calculating loss for an attendee choosing between sessions
    THEN the loss will reflect the attendee joining the preferred session
    """
    test_options = SessionOptions(["Test topic 1", "Test topic 3"])
    assert test_options.calculate_attendee_loss(AttendeePreference("t1", {"Test topic 2": 1})) == 0
    assert test_options.calculate_attendee_loss(AttendeePreference("t1", {"Test topic 1": 1})) == 0
    assert test_options.calculate_attendee_loss(AttendeePreference("t1", {"Test topic 3": 2})) == 0
    assert test_options.calculate_attendee_loss(AttendeePreference("t1", {"Test topic 1": 1, "Test topic 3": 2})) > 0


def test_generate_chooses():
    """
    WHEN choosing all possible subsets of a given set
    THEN all of them will be returned
    """
    # TODO: make set choose comparisons invariant to order - maybe with a class
    # GIGO cases
    assert generate_all_chooses(set(), 1) == []
    assert generate_all_chooses({1}, 2) == []

    # Valid cases
    assert generate_all_chooses({1}, 1) == [({1}, set())]
    assert generate_all_chooses({1, 2}, 2) == [({1, 2}, set())]
    assert generate_all_chooses({1, 2}, 1) == [({1}, {2}), ({2}, {1})]
    assert generate_all_chooses({1, 2, 3}, 3) == [({1, 2, 3}, set())]
    assert generate_all_chooses({1, 2, 3}, 2) == [({1, 2}, {3}), ({1, 3}, {2}), ({2, 3}, {1})]


def test_generate_trivial_session_possibilities():
    """
    WHEN generating trivial session possibilities
    THEN it will not fail unexpectedly
    """
    # Use a single topic in a wide setup to ensure things don't break
    test_topics = {"Test topic 1"}
    trivial_schedules = generate_fixed_width_schedules(test_topics, 3)
    assert len(trivial_schedules) == 1
    assert len(trivial_schedules[0].timeslot_assignments) == 1
    assert trivial_schedules[0].timeslot_assignments[0].sessions == set(test_topics)


def test_generate_wide_session_possibilities():
    """
    WHEN generating wide session possibilities
    THEN they will all be assigned in a single session
    """
    test_topics = {"Test topic 1", "Test topic 2", "Test topic 3"}
    # Allow all 3 to run in parallel so we get a trivial answer
    wide_schedules = generate_fixed_width_schedules(test_topics, 3)
    assert len(wide_schedules) == 1
    assert len(wide_schedules[0].timeslot_assignments) == 1
    assert wide_schedules[0].timeslot_assignments[0].sessions == set(test_topics)


def test_generate_nontrivial_session_possibilities():
    """
    WHEN generating non-trivial session possibilities
    THEN a full set of options will be generated
    """
    test_topics = {"Test topic 1", "Test topic 2", "Test topic 3"}
    nontrivial_schedules = generate_fixed_width_schedules(test_topics, 2)
    assert len(nontrivial_schedules) == 3
    # TODO: de-duplicate


def test_calculate_schedule_losses():
    """
    WHEN assessing a schedule against a set of preferences
    THEN loss is calculated reasonably against all timeslots
    """
    test_schedule = Schedule([
        SessionOptions(["Tt 1", "Tt 3"]),
        SessionOptions(["Tt 2", "Tt 4"])
    ])
    assert test_schedule.calculate_preference_losses([  # No clashes
        AttendeePreference("t1", {"Tt 1": 1, "Tt 2": 2}),
        AttendeePreference("t1", {"Tt 3": 1, "Tt 4": 2}),
    ]) == 0


# def test_generate_all_session_possibilities():
#     """
#     WHEN generating all session possibilities
#     THEN a full set will be generated, even including mixed formats
#     """
#     pass
