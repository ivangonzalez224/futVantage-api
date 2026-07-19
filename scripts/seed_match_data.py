"""Seeds a full, realistic match dataset for testing dashboards:

- One academy, one team, an 11-player roster with real positions.
- One match.
- ~190 domain-valid events (passes, duels, shots, defensive actions,
  set pieces) distributed across the whole squad, weighted so THREE
  tracked players — a center-back, a central midfielder, and a striker
  — get enough volume and variety to build a meaningful individual
  dashboard (pass accuracy, duel win rate, shot efficiency, decisions
  under pressure), while the rest of the squad gets enough coverage for
  team-level aggregates (heatmaps, pass networks, etc).

Every event is built through `get_event_type_rules()`, the same
validation source of truth the API uses, so nothing generated here
could ever fail the real `POST /matches/{id}/events` validation.

Usage:
    .venv/bin/python scripts/seed_match_data.py

Uses a fixed random seed (42), so re-running it produces the exact same
dataset — useful while iterating on dashboards against stable numbers.

-----

"""

import random
from decimal import Decimal
from typing import TypeVar

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domain.event_catalog import EventTypeRules, get_event_type_rules
from app.models import Academy, Event, Match, Player, Team
from app.models.enums import BodyPart, EventResult, EventType, PressureState

random.seed(42)

# (jersey, name, position, zone) — zone is the typical x-range (0-100,
# attacking towards 100) this player operates in, used to place events
# realistically on the court.
ROSTER = [
    (1, "Mateo Salazar", "Portero", (2, 10)),
    (2, "Bruno Castillo", "Lateral derecho", (10, 55)),
    (3, "Renzo Aguilar", "Defensa central", (8, 40)),
    (4, "Diego Ramírez", "Defensa central", (8, 40)),  # tracked: defender
    (5, "Iker Flores", "Lateral izquierdo", (10, 55)),
    (6, "Luis Torres", "Mediocampista defensivo", (25, 60)),
    (8, "Fabrizio Chávez", "Mediocampista", (30, 75)),  # tracked: midfielder
    (10, "Sebastián Rojas", "Mediocampista ofensivo", (40, 85)),
    (7, "Adrián Vargas", "Extremo derecho", (45, 92)),
    (9, "Mauricio Peña", "Delantero centro", (55, 95)),  # tracked: forward
    (11, "Gonzalo Núñez", "Extremo izquierdo", (45, 92)),
]

TRACKED_JERSEYS = {4, 8, 9}
EVENTS_FOR_TRACKED_PLAYER = 28
EVENTS_FOR_OTHER_PLAYER = 14
MATCH_DURATION_SECONDS = 5400  # 90 minutes

# Weighted event-type pools per role. Numbers are relative weights, not counts.
GOALKEEPER_TYPES = [
    (EventType.GOALKEEPER_SAVE, 4),
    (EventType.SHORT_PASS, 3),
    (EventType.LONG_PASS, 2),
    (EventType.CLEARANCE, 2),
]
DEFENDER_TYPES = [
    (EventType.TACKLE_DUEL, 4),
    (EventType.AERIAL_DUEL, 3),
    (EventType.CLEARANCE, 3),
    (EventType.INTERCEPTION, 3),
    (EventType.SHORT_PASS, 4),
    (EventType.LONG_PASS, 2),
]
MIDFIELDER_TYPES = [
    (EventType.SHORT_PASS, 6),
    (EventType.LONG_PASS, 2),
    (EventType.THROUGH_BALL, 2),
    (EventType.TACKLE_DUEL, 2),
    (EventType.DRIBBLE_DUEL, 2),
    (EventType.INTERCEPTION, 2),
    (EventType.SHOT_OPEN_PLAY, 1),
]
FORWARD_TYPES = [
    (EventType.SHOT_OPEN_PLAY, 4),
    (EventType.HEADER_SHOT, 2),
    (EventType.DRIBBLE_DUEL, 4),
    (EventType.SHORT_PASS, 3),
    (EventType.CROSS, 2),
    (EventType.AERIAL_DUEL, 2),
]

ROLE_TYPE_POOLS = {
    "Portero": GOALKEEPER_TYPES,
    "Defensa central": DEFENDER_TYPES,
    "Lateral derecho": DEFENDER_TYPES,
    "Lateral izquierdo": DEFENDER_TYPES,
    "Mediocampista defensivo": DEFENDER_TYPES,
    "Mediocampista": MIDFIELDER_TYPES,
    "Mediocampista ofensivo": MIDFIELDER_TYPES,
    "Extremo derecho": FORWARD_TYPES,
    "Extremo izquierdo": FORWARD_TYPES,
    "Delantero centro": FORWARD_TYPES,
}

# Result weights keyed by which "family" of results a type's rules expose,
# identified by membership rather than by (unordered) set position.
PASS_RESULT_WEIGHTS = [
    (EventResult.COMPLETED, 70),
    (EventResult.INTERCEPTED, 15),
    (EventResult.OUT_OF_BOUNDS, 10),
    (EventResult.BLOCKED, 5),
]
DUEL_RESULT_WEIGHTS = [
    (EventResult.WON, 55),
    (EventResult.LOST, 35),
    (EventResult.FOUL_COMMITTED, 5),
    (EventResult.FOUL_RECEIVED, 5),
]
SHOT_RESULT_WEIGHTS = [
    (EventResult.GOAL, 12),
    (EventResult.SAVED, 35),
    (EventResult.OFF_TARGET, 30),
    (EventResult.POST_OR_CROSSBAR, 8),
    (EventResult.BLOCKED_DEFENDER, 15),
]
DEFENSIVE_RESULT_WEIGHTS = [
    (EventResult.POSSESSION_RETAINED, 55),
    (EventResult.POSSESSION_LOST, 25),
    (EventResult.TO_CORNER_OR_THROW, 20),
]

BODY_PART_WEIGHTS = [
    (BodyPart.RIGHT_FOOT, 55),
    (BodyPart.LEFT_FOOT, 30),
    (BodyPart.HEAD, 15),
]


T = TypeVar("T")


def pick_weighted(options: list[tuple[T, int]]) -> T:
    values = [value for value, _weight in options]
    weights = [weight for _value, weight in options]
    return random.choices(values, weights=weights, k=1)[0]


def pick_result(rules: EventTypeRules) -> EventResult:
    if EventResult.COMPLETED in rules.valid_results:
        return pick_weighted(PASS_RESULT_WEIGHTS)
    if EventResult.GOAL in rules.valid_results:
        return pick_weighted(SHOT_RESULT_WEIGHTS)
    if EventResult.WON in rules.valid_results:
        return pick_weighted(DUEL_RESULT_WEIGHTS)
    return pick_weighted(DEFENSIVE_RESULT_WEIGHTS)


def random_coordinate(zone: tuple[int, int]) -> Decimal:
    return Decimal(str(round(random.uniform(zone[0], zone[1]), 2)))


def random_lateral() -> Decimal:
    return Decimal(str(round(random.uniform(5, 95), 2)))


def build_event(
    match: Match,
    team: Team,
    player: Player,
    zone: tuple[int, int],
    is_shot_zone_override: bool,
) -> Event:
    event_type = pick_weighted(ROLE_TYPE_POOLS[player.position or ""])
    rules = get_event_type_rules(event_type)
    result = pick_result(rules)

    if rules.category.value == "shot" and is_shot_zone_override:
        x_start = random_coordinate((68, 95))
    else:
        x_start = random_coordinate(zone)
    y_start = random_lateral()

    x_end: Decimal | None = None
    y_end: Decimal | None = None
    if rules.requires_destination:
        # Passes generally move the ball forward, towards x=100.
        forward_bias = min(100, float(x_start) + random.uniform(5, 25))
        x_end = Decimal(str(round(forward_bias, 2)))
        y_end = random_lateral()

    pressure: PressureState | None = None
    if rules.allows_pressure:
        pressure = (
            PressureState.UNDER_PRESSURE if random.random() < 0.35 else PressureState.NO_PRESSURE
        )

    body_part: BodyPart | None = None
    if rules.requires_body_part:
        body_part = pick_weighted(BODY_PART_WEIGHTS)

    return Event(
        match=match,
        team=team,
        player=player,
        category=rules.category,
        type=event_type,
        result=result,
        x_start=x_start,
        y_start=y_start,
        x_end=x_end,
        y_end=y_end,
        video_timestamp_seconds=Decimal(str(random.randint(0, MATCH_DURATION_SECONDS))),
        pressure=pressure,
        body_part=body_part,
    )


def main() -> None:
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not set. Check your .env file.")

    engine = create_engine(settings.database_url)

    with Session(engine) as session:
        academy = Academy(name="Academia Real Peru")
        team = Team(name="Sub-15 A", category="Sub-15", academy=academy)
        match = Match(team=team, opponent_name="Rival FC")

        players_by_jersey: dict[int, Player] = {}
        for jersey_number, full_name, position, _zone in ROSTER:
            player = Player(
                jersey_number=jersey_number,
                full_name=full_name,
                position=position,
                team=team,
            )
            players_by_jersey[jersey_number] = player

        session.add(academy)
        session.add(match)
        session.add_all(players_by_jersey.values())

        all_events: list[Event] = []
        for jersey_number, _full_name, _position, zone in ROSTER:
            player = players_by_jersey[jersey_number]
            event_count = (
                EVENTS_FOR_TRACKED_PLAYER
                if jersey_number in TRACKED_JERSEYS
                else EVENTS_FOR_OTHER_PLAYER
            )
            for _ in range(event_count):
                all_events.append(
                    build_event(
                        match=match,
                        team=team,
                        player=player,
                        zone=zone,
                        is_shot_zone_override=True,
                    )
                )

        session.add_all(all_events)
        session.commit()

        print("Dataset de partido sembrado correctamente.\n")
        print(f"TEAM_ID  = {team.id}")
        print(f"MATCH_ID = {match.id}")
        print(f"Total de eventos: {len(all_events)}\n")

        print("Roster:")
        for jersey_number, full_name, position, _zone in ROSTER:
            player = players_by_jersey[jersey_number]
            marker = " <- seguimiento" if jersey_number in TRACKED_JERSEYS else ""
            print(f"  #{jersey_number:<3} {full_name:<20} {position:<25} id={player.id}{marker}")


if __name__ == "__main__":
    main()
