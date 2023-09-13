from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from itertools import islice, permutations
from math import sqrt
from typing import Iterable, Mapping, Set, Tuple

import pandas

TimeslotOptions = Set[str]
Schedule = Set[TimeslotOptions]


@dataclass
class AttendeePreference:
    attendee: str
    preferences: Mapping


def chunk_iterable(iterable, chunk_size):
    # Taken from https://www.geeksforgeeks.org/break-list-chunks-size-n-python/
    iterable = iter(iterable)
    return iter(lambda: tuple(islice(iterable, chunk_size)), ())


def calculate_attendee_loss(
        sessions: TimeslotOptions, attendee_preference: AttendeePreference,
    ) -> float:
    loss = 0
    session_preferences = {
        session_name: attendee_preference.preferences[session_name]
        for session_name in sessions
        if session_name in attendee_preference.preferences
    }
    if session_preferences:
        attended_session = min(session_preferences, key=session_preferences.get)
        del session_preferences[attended_session]
        for missed_preference in session_preferences.values():
            loss += 1 / (sqrt(missed_preference) + 1e-10)
    return loss


def calculate_preference_losses(schedule: Schedule, preferences: Iterable[AttendeePreference]):
    return sum([
        calculate_attendee_loss(option, attendee_preference)
        for option in schedule
        for attendee_preference in preferences
    ])


def extract_attendee_preferences(preferences: pandas.DataFrame) -> Iterable[AttendeePreference]:
    return [
        AttendeePreference(attendee[1].name, attendee[1].dropna().to_dict())
        for attendee in preferences.iterrows()
    ]


def extract_sessions(preferences: pandas.DataFrame):
    return set(preferences.columns.to_list())


def get_preferences_and_sessions_from_file(
        file_name: str
    ) -> Tuple[Iterable[AttendeePreference], TimeslotOptions]:
    preferences_raw = pandas.read_csv(file_name, index_col=0)
    preferences = extract_attendee_preferences(preferences_raw)
    sessions = extract_sessions(preferences_raw)
    return preferences, sessions


def generate_fixed_width_schedules(sessions: Set[str], sessions_per_timeslot: int) -> Set[Schedule]:
    return frozenset([
        frozenset([
            frozenset(chunk)
            for chunk in chunk_iterable(session_order, sessions_per_timeslot)
        ])
        for session_order in permutations(sessions)
    ])


def schedule_str(schedule: Schedule):
    return list(list(timeslot_options) for timeslot_options in schedule)


def main(args: Namespace):
    preferences, sessions = get_preferences_and_sessions_from_file(args.preference_file)
    candidate_schedules = generate_fixed_width_schedules(sessions, args.num_sessions_per_timeslot)
    candidate_losses = [
        (schedule, calculate_preference_losses(schedule, preferences))
        for schedule in candidate_schedules
    ]
    return sorted(candidate_losses, key=lambda tup: tup[1])


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        '-p',
        '--preference-file',
        help="A CSV file of preferences to read",
        required=True,
    )
    parser.add_argument(
        '-n',
        '--num-sessions-per-timeslot',
        default=2,
        help="Number of sessions running in parallel per timeslot",
        type=int,
    )

    args = parser.parse_args()
    candidate_losses = main(args)

    # display some schedules
    schedule, loss = candidate_losses[0]
    print(f"{loss}: {schedule_str(schedule)}\n")
