"""Seeds a minimal but complete dataset for local end-to-end testing:
one academy, one team, a 6-player roster, and one in-progress match.

Reuses the app's own settings/models so it always seeds against
whatever DATABASE_URL is configured in your .env — no hardcoded
credentials here.

Usage:
    .venv/bin/python scripts/seed_demo_data.py

Prints the Team ID and Match ID to paste into the frontend's
/annotate page inputs.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Academy, Match, Player, Team

# Same roster the frontend used to hardcode as SAMPLE_PLAYERS, so the
# jersey numbers you're used to testing with still make sense.
ROSTER = [
    (1, "Mateo Salazar"),
    (4, "Bruno Castillo"),
    (6, "Renzo Aguilar"),
    (8, "Diego Ramírez"),
    (9, "Luis Torres"),
    (10, "Iker Flores"),
]


def main() -> None:
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not set. Check your .env file.")

    engine = create_engine(settings.database_url)

    with Session(engine) as session:
        academy = Academy(name="Academia Real Peru")
        team = Team(name="Sub-15 A", category="Sub-15", academy=academy)
        match = Match(team=team, opponent_name="Rival FC")

        players = [
            Player(jersey_number=jersey_number, full_name=full_name, team=team)
            for jersey_number, full_name in ROSTER
        ]

        session.add(academy)
        session.add(match)
        session.add_all(players)
        session.commit()

        print("Datos sembrados correctamente.\n")
        print(f"TEAM_ID  = {team.id}")
        print(f"MATCH_ID = {match.id}\n")
        print("Roster:")
        for player in players:
            print(f"  #{player.jersey_number:<3} {player.full_name:<20} id={player.id}")


if __name__ == "__main__":
    main()
