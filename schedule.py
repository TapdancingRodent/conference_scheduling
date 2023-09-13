from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from itertools import combinations
from math import sqrt
from typing import Iterable, Mapping, Set, Tuple

import pandas


@dataclass
class AttendeePreference:
    attendee: str
    preferences: Mapping


@dataclass
class SessionOptions:
    sessions: Set[str]

    def calculate_attendee_loss(self, attendee_preference: AttendeePreference) -> float:
        loss = 0
        session_preferences = {
            session_name: attendee_preference.preferences[session_name]
            for session_name in self.sessions
            if session_name in attendee_preference.preferences
        }
        if session_preferences:
            attended_session = min(session_preferences, key=session_preferences.get)
            del session_preferences[attended_session]
            for missed_preference in session_preferences.values():
                loss += 1 / (sqrt(missed_preference) + 1e-10)
        return loss


@dataclass
class Schedule:
    timeslot_assignments: Iterable[SessionOptions]

    def calculate_preference_losses(self, preferences: Iterable[AttendeePreference]):
        return sum([
            option.calculate_attendee_loss(attendee_preference)
            for option in self.timeslot_assignments
            for attendee_preference in preferences
        ])


def extract_attendee_preferences(preferences: pandas.DataFrame) -> Iterable[AttendeePreference]:
    return [
        AttendeePreference(attendee[1].name, attendee[1].dropna().to_dict())
        for attendee in preferences.iterrows()
    ]


def extract_sessions(preferences: pandas.DataFrame):
    return set(preferences.columns.to_list())


def get_preferences_and_sessions_from_file(file_name: str) -> Tuple[Iterable[AttendeePreference], Set[str]]:
    preferences_raw = pandas.read_csv(file_name, index_col=0)
    preferences = extract_attendee_preferences(preferences_raw)
    sessions = extract_sessions(preferences_raw)
    return preferences, sessions


def generate_all_chooses(items: Set, choose_size: int) -> Iterable[Tuple[Set, Set]]:
    chooses = []
    for chosen in combinations(items.copy(), choose_size):
        not_chosen = items.difference(set(chosen))
        chooses.append((set(chosen), set(not_chosen)))
    return chooses


def generate_fixed_width_timeslots(
        sessions: Set[str],
        sessions_per_timeslot: int,
    ) -> Iterable[Iterable[SessionOptions]]:
        if len(sessions) <= sessions_per_timeslot:
            return [[SessionOptions(sessions)]]
        else:
            return [
                [SessionOptions(this_timeslot)] + recursed_options
                for this_timeslot, remaining_sessions
                in generate_all_chooses(sessions, sessions_per_timeslot)
                for recursed_options 
                in generate_fixed_width_timeslots(remaining_sessions, sessions_per_timeslot)
            ]


def generate_fixed_width_schedules(sessions: Set[str], sessions_per_timeslot: int) -> Iterable[Schedule]:
    return [
        Schedule(options) for options in generate_fixed_width_timeslots(sessions, sessions_per_timeslot)
    ]


def main(args: Namespace):
    preferences, sessions = get_preferences_and_sessions_from_file(args.preference_file)
    candidate_schedules = generate_fixed_width_schedules(sessions, 2)
    candidate_losses = [
        (schedule, schedule.calculate_preference_losses(preferences))
        for schedule in candidate_schedules
    ]
    # TODO: deduplicate?
    return sorted(candidate_losses, key=lambda tup: tup[1])


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        '-p',
        '--preference-file',
        help="A CSV file of preferences to read",
        required=True,
    )

    args = parser.parse_args()
    candidate_losses = main(args)

    # display some schedules
    for schedule, loss in candidate_losses[:4]:
        print(f"{loss}:\n{schedule}\n")
