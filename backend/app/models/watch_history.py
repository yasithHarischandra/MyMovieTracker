from sqlalchemy import Integer, String, DateTime, ForeignKey, CheckConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional

from app.database import Base


class WatchHistory(Base):
    __tablename__ = "watch_history"
    __table_args__ = (
        # Exactly one of movie_id or episode_id must be set
        CheckConstraint(
            "(movie_id IS NOT NULL AND episode_id IS NULL) OR (movie_id IS NULL AND episode_id IS NOT NULL)",
            name="ck_watch_history_one_media_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    movie_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=True, index=True)
    episode_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("episodes.id", ondelete="CASCADE"), nullable=True, index=True)

    watched_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1–5, validated at schema layer
    note: Mapped[Optional[str]] = mapped_column(Text)

    movie: Mapped[Optional["Movie"]] = relationship("Movie", back_populates="watch_history")
    episode: Mapped[Optional["Episode"]] = relationship("Episode", back_populates="watch_history")
