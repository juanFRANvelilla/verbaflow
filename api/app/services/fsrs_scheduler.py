from __future__ import annotations

from datetime import datetime, timezone

from fsrs import Card, Rating, Scheduler

_scheduler = Scheduler()


def _state_int(card: Card) -> int:
    state = card.state
    return int(state.value) if hasattr(state, "value") else int(state)


def new_card_now() -> tuple[float, float, datetime, int, int, int]:
    """Estado inicial FSRS: una revisión Good de tarjeta nueva."""
    card, _log = _scheduler.review_card(Card(), Rating.Good)
    due = card.due
    if due.tzinfo is None:
        due = due.replace(tzinfo=timezone.utc)
    return (
        float(card.stability),
        float(card.difficulty),
        due,
        int(card.reps) if hasattr(card, "reps") else 1,
        int(card.lapses) if hasattr(card, "lapses") else 0,
        _state_int(card),
    )


def review_card_state(
    *,
    stability: float,
    difficulty: float,
    due: datetime,
    reps: int,
    lapses: int,
    state: int,
    rating: Rating,
) -> tuple[float, float, datetime, int, int, int, datetime]:
    card = Card()
    card.stability = stability
    card.difficulty = difficulty
    card.due = due if due.tzinfo else due.replace(tzinfo=timezone.utc)
    if hasattr(card, "reps"):
        card.reps = reps
    if hasattr(card, "lapses"):
        card.lapses = lapses
    if hasattr(card, "state"):
        card.state = state

    updated, _log = _scheduler.review_card(card, rating)
    next_due = updated.due
    if next_due.tzinfo is None:
        next_due = next_due.replace(tzinfo=timezone.utc)
    last_review = datetime.now(timezone.utc)
    return (
        float(updated.stability),
        float(updated.difficulty),
        next_due,
        int(getattr(updated, "reps", reps + 1)),
        int(getattr(updated, "lapses", lapses)),
        _state_int(updated),
        last_review,
    )


def rating_from_int(value: int) -> Rating:
    return {
        1: Rating.Again,
        2: Rating.Hard,
        3: Rating.Good,
        4: Rating.Easy,
    }[value]