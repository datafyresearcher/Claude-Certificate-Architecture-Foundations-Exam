"""Batch record processing utilities."""

from __future__ import annotations

from typing import TypedDict


class BatchResult(TypedDict):
    count: int
    average: float
    max_score: float


def process_batch(records: list[dict]) -> BatchResult:
    """Filter active records and compute score statistics.

    Args:
        records: Sequence of record dicts, each expected to have a ``status``
                 string field and a numeric ``score`` field.

    Returns:
        A dict with:
        - ``count``     – number of active records
        - ``average``   – mean score of active records (0.0 when count is 0)
        - ``max_score`` – highest score among active records (0.0 when count is 0)

    Raises:
        TypeError:  if ``records`` is not iterable, or if a score value cannot
                    be compared/summed as a number.
        ValueError: if a record's ``score`` field is present but not convertible
                    to float.
    """
    active_scores: list[float] = [
        float(r["score"])
        for r in records
        if r.get("status") == "active"
    ]

    count = len(active_scores)
    if count == 0:
        return BatchResult(count=0, average=0.0, max_score=0.0)

    return BatchResult(
        count=count,
        average=sum(active_scores) / count,
        max_score=max(active_scores),
    )
