"""Academy model: the organization that owns one or more teams."""

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.team import Team


class Academy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "academies"

    name: Mapped[str] = mapped_column(nullable=False)

    teams: Mapped[list["Team"]] = relationship(back_populates="academy")

    def __repr__(self) -> str:
        return f"Academy(id={self.id!r}, name={self.name!r})"
