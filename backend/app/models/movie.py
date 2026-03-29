from sqlalchemy import Integer, String, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional

from app.database import Base


class Movie(Base):
    __tablename__ = "movies"
    __table_args__ = (UniqueConstraint("tmdb_id", "user_id", name="uq_movie_tmdb_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tmdb_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    overview: Mapped[Optional[str]] = mapped_column(String(5000))
    release_date: Mapped[Optional[Date]] = mapped_column(Date)
    runtime_mins: Mapped[Optional[int]] = mapped_column(Integer)
    genres: Mapped[Optional[str]] = mapped_column(String(500))  # JSON array stored as string
    poster_path: Mapped[Optional[str]] = mapped_column(String(500))
    added_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    watch_history: Mapped[list["WatchHistory"]] = relationship("WatchHistory", back_populates="movie", cascade="all, delete-orphan")
