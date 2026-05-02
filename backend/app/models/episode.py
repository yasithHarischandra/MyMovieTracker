from sqlalchemy import Integer, String, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from app.database import Base


class Episode(Base):
    __tablename__ = "episodes"
    __table_args__ = (UniqueConstraint("season_id", "episode_number", name="uq_episode_season_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    season_id: Mapped[int] = mapped_column(Integer, ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False, index=True)

    episode_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(500))
    runtime_mins: Mapped[Optional[int]] = mapped_column(Integer)
    air_date: Mapped[Optional[Date]] = mapped_column(Date)

    season: Mapped["Season"] = relationship("Season", back_populates="episodes")
    watch_history: Mapped[list["WatchHistory"]] = relationship("WatchHistory", back_populates="episode", cascade="all, delete-orphan")
