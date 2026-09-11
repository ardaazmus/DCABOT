"""Pure policies for non-economic deal lifecycle timing."""


class LifecyclePolicyError(ValueError):
    """Raised when lifecycle policy input violates its bounded contract."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def cooldown_allows_new_deal(
    terminal_effective_time_us: int,
    candidate_effective_time_us: int,
    cooldown_us: int,
) -> bool:
    """Return whether historical time has elapsed for a new deal.

    The policy deliberately accepts only integer ``effective_time_us`` values.
    It has no wall-clock, processing-time, persistence, or economic dependency;
    the caller owns the source and meaning of both historical timestamps.
    The boundary is inclusive: elapsed time equal to ``cooldown_us`` passes.
    """

    if type(terminal_effective_time_us) is not int or type(
        candidate_effective_time_us
    ) is not int:
        raise LifecyclePolicyError(
            "COOLDOWN_TIME_INVALID",
            "Cooldown zamanları integer effective_time_us olmalıdır.",
        )
    if type(cooldown_us) is not int or cooldown_us < 0:
        raise LifecyclePolicyError(
            "COOLDOWN_INVALID", "Cooldown süresi negatif olamaz.",
        )
    if candidate_effective_time_us < terminal_effective_time_us:
        raise LifecyclePolicyError(
            "COOLDOWN_TIME_ORDER_INVALID",
            "Aday effective_time_us terminal zamandan önce olamaz.",
        )
    return (
        candidate_effective_time_us - terminal_effective_time_us
    ) >= cooldown_us
