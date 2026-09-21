"""Overfitting scores: PBO/CSCV and DSR over finalized trial results.

Reads ``trial_registry`` studies without mutating them: only SUCCEEDED
trials with caller-supplied finalized returns enter the computation;
FAILED/INVALID trials are ignored but never dropped from the registry.
Returns arrive as Decimal strings and cross into float64 only inside
``dcabot.analytics`` (advisory scores, never ledger inputs).
"""

from itertools import combinations

from dcabot.analytics.scores import (
    AnalyticsError,
    deflated_sharpe_ratio,
    kurtosis_excess,
    sharpe_ratio,
    skewness,
    to_float_series,
)
from dcabot.application.trial_registry import TrialStudy, TrialStatus


class OverfittingProbabilityError(ValueError):
    """Raised when an overfitting score cannot be computed honestly."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def probability_of_backtest_overfitting(
    study: TrialStudy,
    returns_by_trial: dict[str, tuple[str, ...]],
    *,
    block_count: int,
) -> float:
    """Return Bailey et al.'s PBO via the CSCV procedure.

    The T-period return series of each SUCCEEDED config is cut into
    ``block_count`` (even) blocks; every C(S,S/2) half-split picks its
    in-sample winner and records that winner's out-of-sample relative
    rank omega = rank/(N+1) (ascending, ties broken by trial id). PBO
    is the fraction of splits with omega < 0.5 (logit < 0).
    """

    if type(study) is not TrialStudy:
        raise OverfittingProbabilityError("PBO_STUDY_INVALID", "Study güvenli tipte olmalıdır.")
    if not isinstance(returns_by_trial, dict):
        raise OverfittingProbabilityError("PBO_RETURNS_INVALID", "Returns dict olmalıdır.")
    if type(block_count) is not int or block_count < 2 or block_count % 2 != 0:
        raise OverfittingProbabilityError("PBO_BLOCKS_INVALID", "Blok sayısı çift ve ≥2 olmalıdır.")
    succeeded = sorted(
        trial.trial_id for trial in study.trials if trial.status == TrialStatus.SUCCEEDED
    )
    if len(succeeded) < 2:
        raise OverfittingProbabilityError("PBO_CONFIGS_TOO_FEW", "PBO en az 2 SUCCEEDED config ister.")
    missing = [trial_id for trial_id in succeeded if trial_id not in returns_by_trial]
    if missing:
        raise OverfittingProbabilityError(
            "PBO_RETURNS_COVERAGE_INVALID", f"Returnu eksik config: {missing[0]}."
        )
    series: dict[str, tuple[float, ...]] = {}
    for trial_id in succeeded:
        raw = returns_by_trial[trial_id]
        if not isinstance(raw, tuple):
            raise OverfittingProbabilityError("PBO_RETURNS_INVALID", "Return serileri tuple olmalıdır.")
        try:
            series[trial_id] = to_float_series(raw)
        except AnalyticsError as error:
            raise OverfittingProbabilityError("PBO_RETURNS_INVALID", "Return serisi geçersiz.") from error
    periods = {len(values) for values in series.values()}
    if len(periods) != 1:
        raise OverfittingProbabilityError("PBO_PERIODS_RAGGED", "Tüm config'ler aynı T uzunluğunda olmalıdır.")
    total = periods.pop()
    if total < block_count or total % block_count != 0:
        raise OverfittingProbabilityError(
            "PBO_PERIODS_BLOCK_MISMATCH", "T blok sayısına tam bölünmelidir."
        )
    width = total // block_count
    blocks = tuple(range(block_count))
    half = block_count // 2
    overfit = 0
    splits = 0
    for in_sample in combinations(blocks, half):
        in_set = set(in_sample)
        out_set = set(blocks) - in_set
        in_means = {trial_id: _block_mean(series[trial_id], in_set, width) for trial_id in succeeded}
        best = min(succeeded, key=lambda trial_id: (-in_means[trial_id], trial_id))
        out_means = {trial_id: _block_mean(series[trial_id], out_set, width) for trial_id in succeeded}
        ordered = sorted(succeeded, key=lambda trial_id: (out_means[trial_id], trial_id))
        rank = ordered.index(best) + 1
        omega = rank / (len(succeeded) + 1)
        if omega < 0.5:
            overfit += 1
        splits += 1
    return overfit / splits


def deflated_sharpe_for_returns(returns: tuple[str, ...], *, n_trials: int) -> float:
    """Score one finalized return series with the Deflated Sharpe Ratio."""

    if type(n_trials) is not int or n_trials < 1:
        raise OverfittingProbabilityError(
            "DSR_TRIALS_INVALID", "Deneme sayısı pozitif integer olmalıdır."
        )
    try:
        series = to_float_series(returns)
        score = deflated_sharpe_ratio(
            sharpe=sharpe_ratio(series),
            n_obs=len(series),
            skew=skewness(series),
            kurt=kurtosis_excess(series) + 3.0,
            n_trials=n_trials,
        )
    except AnalyticsError as error:
        raise OverfittingProbabilityError("DSR_SCORING_INVALID", "DSR skoru hesaplanamadı.") from error
    return score


def _block_mean(series: tuple[float, ...], blocks: set[int], width: int) -> float:
    total = 0.0
    count = 0
    for block in blocks:
        for offset in range(width):
            total += series[block * width + offset]
            count += 1
    return total / count
