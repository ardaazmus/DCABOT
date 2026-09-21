"""Chart draft-level validation (F29).

A dragged level is a display proposal until the backend accepts it against
the verified dataset range. This core decides the verdict; the route binds
it to the dataset revision (artifact hash).
"""
from dcabot.domain.numbers import exact_text, number


class DraftLevelError(ValueError):
    """Raised when a draft level cannot be judged safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def validate_draft_level(*, low: str, high: str, draft_price: str) -> dict[str, str]:
    """Accept a draft price inside the verified range, else reject."""
    try:
        floor = number(low)
        ceiling = number(high)
        draft = number(draft_price)
    except ValueError as error:
        raise DraftLevelError(
            "DRAFT_PRICE_INVALID", "Taslak fiyat exact decimal olmalıdır."
        ) from error
    if floor > ceiling:
        raise DraftLevelError("DRAFT_RANGE_INVALID", "Aralık ters olamaz.")
    if not floor <= draft <= ceiling:
        return {
            "verdict": "REJECTED",
            "draft_price": exact_text(draft),
            "reason": "Taslak seviye grafik aralığının dışında.",
        }
    return {
        "verdict": "ACCEPTED",
        "draft_price": exact_text(draft),
        "reason": "Taslak seviye aralık içinde.",
    }
