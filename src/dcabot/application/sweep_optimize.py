"""Faz 15.7: sampler + sweep tek çağrıda (Optimize).

14.6 sampler'ı tarif önerir, 14.5 sweep'i sıralı koşar, sonuçlar
`realized_net_after_all_costs` metriğine göre exact Fraction
karşılaştırmayla sıralanır. Eşitlikte öneri sırası korunur (stabil).
Float örnekler IEEE-754 repr exact metnine çevrilir; config'e
string girer, sayı hesabı Fraction'dadır.
"""

from fractions import Fraction
from typing import Final

from dcabot.application.sweep_orchestrator import SweepError, run_parameter_sweep
from dcabot.application.trial_sampler import (
    GridSampler,
    RandomSampler,
    StudySpace,
    TrialSamplerError,
    suggest_trial_params,
)
from dcabot.data_adapters.historical import HistoricalDatasetInput


_MAX_TRIALS: Final = 32


class SweepOptimizeError(ValueError):
    """Raised when an optimize request cannot run honestly."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def _freeze(value: object) -> object:
    if isinstance(value, bool):
        raise SweepOptimizeError("OPTIMIZE_VALUE_INVALID", "Bool override kabul edilmez.")
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return value
    raise SweepOptimizeError("OPTIMIZE_VALUE_INVALID", "Override yalnız int/float/str olabilir.")


def suggest_recipes(
    space: dict, *, max_trials: int, seed: int, sampler: str
) -> tuple[tuple[dict, ...], int]:
    """Suggest bounded recipes; identical parameter sets run once."""

    if sampler == "grid":
        sampler_impl = GridSampler()
    elif sampler == "random":
        sampler_impl = RandomSampler(seed=seed)
    else:
        raise TrialSamplerError("SAMPLER_NAME_INVALID", "sampler yalnız grid ya da random olabilir.")
    study = StudySpace(space)
    seen: set[tuple] = set()
    recipes: list[dict] = []
    suggested = 0
    for _ in range(max_trials):
        params = suggest_trial_params(sampler_impl, study)
        suggested += 1
        signature = tuple(sorted((name, _freeze(value)) for name, value in params.items()))
        if signature in seen:
            continue
        seen.add(signature)
        overrides = {name: value for name, value in signature}
        recipes.append({"recipe_id": f"trial-{len(recipes) + 1}", "overrides": overrides})
    return tuple(recipes), suggested


def _metric_of(summary: dict) -> Fraction:
    raw = summary.get("realized_net_after_all_costs")
    if not isinstance(raw, str):
        raise SweepOptimizeError("OPTIMIZE_METRIC_INVALID", "Metrik exact decimal string değil.")
    try:
        return Fraction(raw)
    except (ValueError, ZeroDivisionError) as error:
        raise SweepOptimizeError("OPTIMIZE_METRIC_INVALID", "Metrik parse edilemedi.") from error


def optimize_parameters(
    dataset: HistoricalDatasetInput,
    base_config: dict,
    *,
    space: dict,
    max_trials: int,
    seed: int,
    sampler: str,
) -> dict:
    """Run sampler + sequential sweep, rank by exact net metric."""

    if type(max_trials) is not int or not 1 <= max_trials <= _MAX_TRIALS:
        raise SweepOptimizeError("OPTIMIZE_TRIALS_INVALID", "max_trials 1-32 integer olmalıdır.")
    if type(seed) is not int:
        raise SweepOptimizeError("OPTIMIZE_SEED_INVALID", "seed integer olmalıdır.")
    if not isinstance(dataset, HistoricalDatasetInput):
        raise SweepOptimizeError("OPTIMIZE_DATASET_INVALID", "Dataset güvenli tipte olmalıdır.")
    if not isinstance(base_config, dict):
        raise SweepOptimizeError("OPTIMIZE_CONFIG_INVALID", "Base config dict olmalıdır.")
    recipes, suggested = suggest_recipes(space, max_trials=max_trials, seed=seed, sampler=sampler)
    if not recipes:
        raise SweepOptimizeError("OPTIMIZE_EMPTY_INVALID", "Hiç tarif üretilemedi.")
    trials = []
    skipped: list[dict] = []
    first_error: SweepError | None = None
    for recipe in recipes:
        try:
            (result,) = run_parameter_sweep(
                (recipe,), base_config=dict(base_config), dataset=dataset, max_workers=1
            )
        except SweepError as error:
            if first_error is None:
                first_error = error
            skipped.append(
                {"recipe_id": recipe["recipe_id"], "overrides": recipe["overrides"], "code": error.code}
            )
            continue
        metric = _metric_of(result["summary"])
        trials.append(
            {
                "recipe_id": result["recipe_id"],
                "overrides": recipe["overrides"],
                "execution_status": result["execution_status"],
                "realized_net_after_all_costs": result["summary"]["realized_net_after_all_costs"],
                "config_hash": result["config_hash"],
                "_metric": metric,
            }
        )
    if not trials:
        assert first_error is not None
        raise first_error
    trials.sort(key=lambda trial: trial["_metric"], reverse=True)
    best = trials[0]
    for trial in trials:
        del trial["_metric"]
    return {
        "sampler": sampler,
        "seed": seed,
        "suggested_count": suggested,
        "trial_count": len(trials),
        "trials": trials,
        "skipped_count": len(skipped),
        "skipped": skipped,
        "best_recipe_id": best["recipe_id"],
        "best_overrides": best["overrides"],
        "best_metric": best["realized_net_after_all_costs"],
    }
