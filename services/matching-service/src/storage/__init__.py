"""Storage package exposing ORM-like helpers."""

from .database import (
    count_rows,
    create_matches,
    create_swipe,
    create_user,
    fetch_matches_for_user,
    fetch_swipe_events,
    get_user,
    has_mutual_like,
    init_db,
    list_users,
    log_swipe_event,
    reset_database,
    reset_engine,
    upsert_user,
)
from .models import Match, MatchScore, Swipe, SwipeEvent, User

__all__ = [
    "Match",
    "MatchScore",
    "Swipe",
    "SwipeEvent",
    "User",
    "count_rows",
    "create_matches",
    "create_swipe",
    "create_user",
    "list_users",
    "fetch_matches_for_user",
    "fetch_swipe_events",
    "get_user",
    "has_mutual_like",
    "init_db",
    "log_swipe_event",
    "reset_database",
    "reset_engine",
    "upsert_user",
]

