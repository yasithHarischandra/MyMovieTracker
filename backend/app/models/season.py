from sqlalchemy import Integer, String, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from app.database import Base


class Season(Base):
    __tablename__ = "seasons"
    __table_args__ = (UniqueConstraint("show_id", "season_number", name="uq_season_show_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    show_id: Mapped[int] = mapped_column(Integer, ForeignKey("tv_shows.id", ondelete="CASCADE"), nullable=False, index=True)

    season_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(500))
    episode_count: Mapped[int] = mapped_column(Integer, default=0)
    air_date: Mapped[Optional[Date]] = mapped_column(Date)

    show: Mapped["TvShow"] = relationship("TvShow", back_populates="seasons")
    episodes: Mapped[list["Episode"]] = relationship("Episode", back_populates="season", cascade="all, delete-orphan", order_by="Episode.episode_number")
