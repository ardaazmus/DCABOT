"""Faz 14.6: deneme-öncesi sampler arayüzü (registry tek doğruluk kaynağı).

Bir sampler YALNIZ parametre önerir: deneme kaydı (register_trial)
ve sonuç her zaman trial_registry'dedir. Yerleşik sampler'lar
stdlib-only ve deterministiktir (seed'li). Optuna adaptörü ask-tell
kullanır, sampler rolünde kalır ve kurulu değilse açıkça reddeder.
"""

from itertools import product
import random


class TrialSamplerError(ValueError):
    """Raised when a trial suggestion cannot be produced honestly."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class StudySpace:
    """Bounded parameter definitions shared by every sampler."""

    def __init__(self, definitions: dict) -> None:
        if not isinstance(definitions, dict) or not definitions:
            raise TrialSamplerError("SAMPLER_SPACE_INVALID", "Space boş olmayan dict olmalıdır.")
        cleaned: dict[str, dict] = {}
        for name, spec in definitions.items():
            if not isinstance(name, str) or not name:
                raise TrialSamplerError("SAMPLER_SPACE_INVALID", "Parametre adı geçersiz.")
            if not isinstance(spec, dict):
                raise TrialSamplerError("SAMPLER_SPACE_INVALID", f"{name}: spec dict olmalıdır.")
            kind = spec.get("kind")
            if kind == "float":
                low, high = spec.get("low"), spec.get("high")
                if (
                    not isinstance(low, (int, float))
                    or not isinstance(high, (int, float))
                    or isinstance(low, bool)
                    or isinstance(high, bool)
                    or not low < high
                ):
                    raise TrialSamplerError("SAMPLER_SPACE_INVALID", f"{name}: float low<high ister.")
                cleaned[name] = {"kind": "float", "low": float(low), "high": float(high)}
            elif kind == "int":
                low, high = spec.get("low"), spec.get("high")
                if type(low) is not int or type(high) is not int or not low <= high:
                    raise TrialSamplerError("SAMPLER_SPACE_INVALID", f"{name}: int low<=high ister.")
                cleaned[name] = {"kind": "int", "low": low, "high": high}
            elif kind == "categorical":
                choices = spec.get("choices")
                if (
                    not isinstance(choices, (tuple, list))
                    or not choices
                    or not all(isinstance(choice, str) for choice in choices)
                ):
                    raise TrialSamplerError(
                        "SAMPLER_SPACE_INVALID", f"{name}: choices boş olmayan string listesi ister."
                    )
                cleaned[name] = {"kind": "categorical", "choices": tuple(choices)}
            else:
                raise TrialSamplerError(
                    "SAMPLER_SPACE_INVALID", f"{name}: kind float/int/categorical olmalıdır."
                )
        self._definitions = cleaned

    def param_names(self) -> tuple:
        return tuple(self._definitions)

    def definition(self, name: str) -> dict:
        return dict(self._definitions[name])


class RandomSampler:
    """Seeded uniform sampler (stdlib-only, reproducible)."""

    def __init__(self, *, seed: int = 0) -> None:
        if type(seed) is not int:
            raise TrialSamplerError("SAMPLER_SEED_INVALID", "Seed integer olmalıdır.")
        self._random = random.Random(seed)

    def suggest(self, space: StudySpace) -> dict:
        params: dict = {}
        for name in space.param_names():
            spec = space.definition(name)
            if spec["kind"] == "float":
                params[name] = self._random.uniform(spec["low"], spec["high"])
            elif spec["kind"] == "int":
                params[name] = self._random.randint(spec["low"], spec["high"])
            else:
                params[name] = self._random.choice(spec["choices"])
        return params

    def observe(self, trial_id: str, value: float) -> None:
        """Accept an outcome (random sampling ignores history by design)."""

        if not isinstance(trial_id, str) or not trial_id:
            raise TrialSamplerError("SAMPLER_OBSERVE_INVALID", "trial_id geçersiz.")
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TrialSamplerError("SAMPLER_OBSERVE_INVALID", "value sayı olmalıdır.")


class GridSampler:
    """Deterministic cartesian-grid sampler (floats use 3 points)."""

    def __init__(self) -> None:
        self._cursor = 0

    def suggest(self, space: StudySpace) -> dict:
        names = space.param_names()
        axes = []
        for name in names:
            spec = space.definition(name)
            if spec["kind"] == "float":
                low, high = spec["low"], spec["high"]
                axes.append((low, (low + high) / 2.0, high))
            elif spec["kind"] == "int":
                axes.append(tuple(range(spec["low"], spec["high"] + 1)))
            else:
                axes.append(spec["choices"])
        combos = list(product(*axes))
        pick = combos[self._cursor % len(combos)]
        self._cursor += 1
        return dict(zip(names, pick))

    def observe(self, trial_id: str, value: float) -> None:
        if not isinstance(trial_id, str) or not trial_id:
            raise TrialSamplerError("SAMPLER_OBSERVE_INVALID", "trial_id geçersiz.")
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TrialSamplerError("SAMPLER_OBSERVE_INVALID", "value sayı olmalıdır.")


class OptunaSampler:
    """Ask-tell adapter: Optuna suggests, the registry still records.

    Requires the optional ``optuna`` package. When it is installed the
    adapter maps StudySpace to distributions and relays observations
    through study.tell; the registry remains the source of truth and
    Optuna storage stays in-memory (no silent persistence).
    """

    def __init__(self, *, seed: int = 0) -> None:
        try:
            import optuna
        except ImportError as error:
            raise TrialSamplerError(
                "SAMPLER_OPTUNA_MISSING",
                "Optuna kurulu değil; RandomSampler/GridSampler kullanın.",
            ) from error
        if type(seed) is not int:
            raise TrialSamplerError("SAMPLER_SEED_INVALID", "Seed integer olmalıdır.")
        self._optuna = optuna
        self._study = optuna.create_study(
            sampler=optuna.samplers.TPESampler(seed=seed),
            direction="maximize",
        )
        self._pending: dict[str, object] = {}

    def suggest(self, space: StudySpace) -> dict:
        trial = self._study.ask()
        params: dict = {}
        for name in space.param_names():
            spec = space.definition(name)
            if spec["kind"] == "float":
                params[name] = trial.suggest_float(name, spec["low"], spec["high"])
            elif spec["kind"] == "int":
                params[name] = trial.suggest_int(name, spec["low"], spec["high"])
            else:
                params[name] = trial.suggest_categorical(name, list(spec["choices"]))
        self._pending_key = getattr(self, "_pending_key", 0) + 1
        self._pending[str(self._pending_key)] = trial
        self._last_trial = trial
        return params

    def observe(self, trial_id: str, value: float) -> None:
        if not isinstance(trial_id, str) or not trial_id:
            raise TrialSamplerError("SAMPLER_OBSERVE_INVALID", "trial_id geçersiz.")
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TrialSamplerError("SAMPLER_OBSERVE_INVALID", "value sayı olmalıdır.")
        trial = getattr(self, "_last_trial", None)
        if trial is None:
            raise TrialSamplerError("SAMPLER_OBSERVE_INVALID", "Önce suggest çağrılmalıdır.")
        self._study.tell(trial, float(value))
        self._last_trial = None


def suggest_trial_params(sampler, space: StudySpace) -> dict:
    """Suggest one parameter set through any sampler implementation."""

    if not isinstance(space, StudySpace):
        raise TrialSamplerError("SAMPLER_SPACE_INVALID", "Space güvenli tipte olmalıdır.")
    suggest = getattr(sampler, "suggest", None)
    if not callable(suggest):
        raise TrialSamplerError("SAMPLER_INTERFACE_INVALID", "Sampler suggest() sağlamalıdır.")
    params = suggest(space)
    if not isinstance(params, dict) or set(params) != set(space.param_names()):
        raise TrialSamplerError("SAMPLER_PARAMS_INVALID", "Öneri space'i tam kapsamalıdır.")
    return params
