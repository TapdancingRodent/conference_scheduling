from schedule import (
    AttendeePreference,
    calculate_attendee_loss,
    calculate_preference_losses,
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
    test_options = frozenset(["Test topic 1", "Test topic 3"])
    assert calculate_attendee_loss(test_options, AttendeePreference("t1", {"Test topic 2": 1})) == 0
    assert calculate_attendee_loss(test_options, AttendeePreference("t1", {"Test topic 1": 1})) == 0
    assert calculate_attendee_loss(test_options, AttendeePreference("t1", {"Test topic 3": 2})) == 0
    assert calculate_attendee_loss(test_options, AttendeePreference("t1", {"Test topic 1": 1, "Test topic 3": 2})) > 0


def test_generate_trivial_session_possibilities():
    """
    WHEN generating trivial session possibilities
    THEN it will not fail unexpectedly
    """
    # Use a single topic in a wide setup to ensure things don't break
    test_topics = {"Test topic 1"}
    trivial_schedules = generate_fixed_width_schedules(test_topics, 3)
    assert len(trivial_schedules) == 1
    assert len(list(trivial_schedules)[0]) == 1
    assert list(list(trivial_schedules)[0])[0] == frozenset(test_topics)


def test_generate_wide_session_possibilities():
    """
    WHEN generating wide session possibilities
    THEN they will all be assigned in a single session
    """
    test_topics = {"Test topic 1", "Test topic 2", "Test topic 3"}
    # Allow all 3 to run in parallel so we get a trivial answer
    wide_schedules = generate_fixed_width_schedules(test_topics, 3)
    assert len(wide_schedules) == 1
    assert len(list(wide_schedules)[0]) == 1
    assert list(list(wide_schedules)[0])[0] == frozenset(test_topics)


def test_generate_nontrivial_session_possibilities():
    """
    WHEN generating non-trivial session possibilities
    THEN a full set of options will be generated
    """
    test_topics = {"Test topic 1", "Test topic 2", "Test topic 3"}
    nontrivial_schedules = generate_fixed_width_schedules(test_topics, 2)
    assert len(nontrivial_schedules) == 3
    # TODO: Richer inspection


def test_calculate_schedule_losses():
    """
    WHEN assessing a schedule against a set of preferences
    THEN loss is calculated reasonably against all timeslots
    """
    test_schedule = frozenset([
        frozenset(["Tt 1", "Tt 3"]),
        frozenset(["Tt 2", "Tt 4"])
    ])
    assert calculate_preference_losses(
        test_schedule,
        [  # No clashes
            AttendeePreference("t1", {"Tt 1": 1, "Tt 2": 2}),
            AttendeePreference("t1", {"Tt 3": 1, "Tt 4": 2}),
        ]
    ) == 0


# def test_generate_all_session_possibilities():
#     """
#     WHEN generating all session possibilities
#     THEN a full set will be generated, even including mixed formats
#     """
#     pass
