from sqlalchemy import Integer, String, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional

from app.database import Base


class TvShow(Base):
    __tablename__ = "tv_shows"
    __table_args__ = (UniqueConstraint("tmdb_id", "user_id", name="uq_show_tmdb_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tmdb_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    overview: Mapped[Optional[str]] = mapped_column(String(5000))
    first_air_date: Mapped[Optional[Date]] = mapped_column(Date)
    genres: Mapped[Optional[str]] = mapped_column(String(500))
    status: Mapped[Optional[str]] = mapped_column(String(100))  # e.g. "Returning Series", "Ended"
    poster_path: Mapped[Optional[str]] = mapped_column(String(500))
    added_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_synced_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))

    seasons: Mapped[list["Season"]] = relationship("Season", back_populates="show", cascade="all, delete-orphan", order_by="Season.season_number")
