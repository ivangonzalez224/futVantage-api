"""Tests for the Academy / Team / Player models: relationships, constraints
and defaults.
"""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Academy, Player, Team


def test_creates_academy_team_and_player_with_relationships(db_session: Session) -> None:
    academy = Academy(name="Academia Real Peru")
    team = Team(name="Sub-15 A", category="Sub-15", academy=academy)
    player = Player(jersey_number=8, full_name="Diego Ramirez", team=team)

    db_session.add(academy)
    db_session.commit()

    assert team.academy is academy
    assert player.team is team
    assert player in team.players
    assert team in academy.teams


def test_created_at_is_set_automatically(db_session: Session) -> None:
    academy = Academy(name="Academia Real Peru")

    db_session.add(academy)
    db_session.commit()

    assert academy.created_at is not None


def test_rejects_duplicate_jersey_number_within_the_same_team(db_session: Session) -> None:
    academy = Academy(name="Academia Real Peru")
    team = Team(name="Sub-15 A", category="Sub-15", academy=academy)
    db_session.add(academy)
    db_session.add(Player(jersey_number=8, full_name="Diego Ramirez", team=team))
    db_session.commit()

    db_session.add(Player(jersey_number=8, full_name="Otro Jugador", team=team))

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_allows_the_same_jersey_number_on_different_teams(db_session: Session) -> None:
    academy = Academy(name="Academia Real Peru")
    team_a = Team(name="Sub-15 A", category="Sub-15", academy=academy)
    team_b = Team(name="Sub-15 B", category="Sub-15", academy=academy)
    db_session.add(academy)
    db_session.add(Player(jersey_number=8, full_name="Diego Ramirez", team=team_a))
    db_session.add(Player(jersey_number=8, full_name="Luis Torres", team=team_b))

    db_session.commit()  # should not raise

    assert team_a.players[0].jersey_number == team_b.players[0].jersey_number


def test_team_requires_an_academy(db_session: Session) -> None:
    team = Team(name="Sub-15 A", category="Sub-15")
    db_session.add(team)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_player_position_and_birth_date_are_optional(db_session: Session) -> None:
    academy = Academy(name="Academia Real Peru")
    team = Team(name="Sub-15 A", category="Sub-15", academy=academy)
    player = Player(jersey_number=1, full_name="Mateo Salazar", team=team)

    db_session.add(academy)
    db_session.commit()

    assert player.position is None
    assert player.birth_date is None
