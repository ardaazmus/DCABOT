"""Faz 17 AA.7c (WF/MC): overfitting assessment across one parameter sweep.

Reuses the exact same recipe-suggestion + sequential-sweep primitives
`sweep_optimize.optimize_parameters` does (`suggest_recipes`,
`run_parameter_sweep`) -- no new sweep mechanism. Each SUCCEEDED trial's
bar-over-bar equity returns (`equity_curve_scores.bar_returns`, itself
already exact-Fraction-then-float-boundary) become its return series;
`trial_registry.TrialStudy` (already-tested, in-memory, no persistence)
tracks every attempt honestly (FAILED/INVALID trials are never dropped,
only excluded from PBO's own equal-length requirement); `overfitting_
probability.py`'s already-tested PBO/DSR (Bailey et al.) score the result.
No new statistics -- only wiring three already-tested modules together.
"""

from dcabot.application.equity_curve_scores import bar_returns
from dcabot.application.overfitting_probability import (
    OverfittingProbabilityError,
    deflated_sharpe_for_returns,
    probability_of_backtest_overfitting,
)
from dcabot.application.sweep_optimize import suggest_recipes
from dcabot.application.sweep_orchestrator import SweepError, run_parameter_sweep
from dcabot.application.trial_registry import TrialRecord, TrialStatus, new_trial_study, register_trial
from dcabot.data_adapters.historical import HistoricalDatasetInput


class SweepOverfittingError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def assess_sweep_overfitting(
    dataset: HistoricalDatasetInput,
    base_config: dict,
    *,
    space: dict,
    max_trials: int,
    seed: int,
    sampler: str,
    block_count: int,
) -> dict:
    """Run the sweep, then score it for overfitting (PBO across all
    SUCCEEDED trials + each SUCCEEDED trial's own DSR). A trial is
    SUCCEEDED only if it ran to completion AND its bar-return series is
    the same length as the first SUCCEEDED trial's -- PBO/CSCV requires
    identical T across configs (Bailey et al.); a shorter/ambiguous run
    (e.g. INDETERMINATE) is recorded INVALID, never silently padded or
    truncated to fit."""

    if not isinstance(dataset, HistoricalDatasetInput):
        raise SweepOverfittingError("OVERFIT_DATASET_INVALID", "Dataset güvenli tipte olmalıdır.")
    if not isinstance(base_config, dict):
        raise SweepOverfittingError("OVERFIT_CONFIG_INVALID", "Base config dict olmalıdır.")
    try:
        recipes, suggested = suggest_recipes(space, max_trials=max_trials, seed=seed, sampler=sampler)
    except (SweepError, ValueError) as error:
        raise SweepOverfittingError("OVERFIT_RECIPE_INVALID", str(error)) from error
    if not recipes:
        raise SweepOverfittingError("OVERFIT_EMPTY_INVALID", "Hiç tarif üretilemedi.")

    study = new_trial_study(
        "sweep-overfit",
        parameter_space_id="sweep-space",
        objective_id="realized_net_after_all_costs",
        selection_rule_id="max",
        max_trials=max(len(recipes), 1),
    )
    returns_by_trial: dict[str, tuple[str, ...]] = {}
    expected_length: int | None = None
    skipped: list[dict] = []
    for recipe in recipes:
        trial_id = recipe["recipe_id"]
        try:
            (result,) = run_parameter_sweep(
                (recipe,), base_config=dict(base_config), dataset=dataset, max_workers=1
            )
        except SweepError as error:
            study, _ = register_trial(study, TrialRecord(trial_id=trial_id, status=TrialStatus.FAILED))
            skipped.append({"recipe_id": trial_id, "code": error.code})
            continue
        summary = result["summary"]
        equity_curve = tuple(summary.get("equity_curve", ()))
        returns = bar_returns(equity_curve) if len(equity_curve) >= 2 else ()
        is_complete = result["execution_status"] == "COMPLETED"
        if is_complete and len(returns) >= 2 and (expected_length is None or len(returns) == expected_length):
            expected_length = len(returns) if expected_length is None else expected_length
            status = TrialStatus.SUCCEEDED
            returns_by_trial[trial_id] = returns
        else:
            status = TrialStatus.INVALID
        study, _ = register_trial(
            study, TrialRecord(trial_id=trial_id, status=status, parameter_hash=result["config_hash"])
        )

    succeeded = [trial.trial_id for trial in study.trials if trial.status == TrialStatus.SUCCEEDED]
    pbo: str | None = None
    if len(succeeded) >= 2:
        try:
            pbo = repr(
                probability_of_backtest_overfitting(study, returns_by_trial, block_count=block_count)
            )
        except OverfittingProbabilityError:
            pbo = None
    dsr_by_trial: dict[str, str | None] = {}
    n_trials = max(len(succeeded), 1)
    for trial_id in succeeded:
        try:
            dsr_by_trial[trial_id] = repr(
                deflated_sharpe_for_returns(returns_by_trial[trial_id], n_trials=n_trials)
            )
        except OverfittingProbabilityError:
            dsr_by_trial[trial_id] = None

    return {
        "sampler": sampler,
        "seed": seed,
        "suggested_count": suggested,
        "trial_count": len(recipes),
        "succeeded_count": len(succeeded),
        "skipped_count": len(skipped),
        "skipped": skipped,
        "return_series_length": expected_length,
        "block_count": block_count,
        "pbo": pbo,
        "dsr_by_trial": dsr_by_trial,
    }
