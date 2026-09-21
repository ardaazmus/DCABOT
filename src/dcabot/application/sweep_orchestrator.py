"""Faz 14.5: bar-cache'li parametre sweep orkestratörü.

Reducer (simulate_historical_ohlcv) aynen korunur; ölçek yalnız
süreç düzeyinde gelir:
- max_workers=1: işlem-içi sıralı koşu (belirleyici, pickle yok).
- max_workers>1: ProcessPoolExecutor + worker-initializer bar-cache;
  dataset her worker'a bir kez yüklenir, tarif başına yeniden parse
  edilmez. Sonuçlar tarif sırasında döner.

Windows spawn güvenliği: worker fonksiyonları modül-seviyesindedir.
Her task tam raw_config taşır; worker base config bilmez.
"""

from concurrent.futures import ProcessPoolExecutor
import hashlib
import pickle
from pathlib import Path
import re

from dcabot.application.historical_run_contract import canonical_json
from dcabot.application.historical_simulation import simulate_historical_ohlcv
from dcabot.data_adapters.historical import HistoricalDatasetInput
from dcabot.domain.config import Config


_RECIPE_ID = re.compile(r"[A-Za-z0-9_.:-]{1,100}\Z", re.ASCII)
_SWEEPABLE = frozenset(
    {
        "base_qty",
        "safety_qty",
        "safety_count",
        "deviation",
        "step_multiplier",
        "volume_multiplier",
        "take_profit",
    }
)
_MAX_WORKERS = 16
_MAX_RECIPES = 4096

_SWEEP_DATASET = None


class SweepError(ValueError):
    """Raised when a parameter sweep cannot run honestly."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def write_sweep_cache(dataset: HistoricalDatasetInput, cache_path: Path) -> None:
    """Persist one dataset for worker-initializer loading (single write)."""

    if not isinstance(dataset, HistoricalDatasetInput):
        raise SweepError("SWEEP_DATASET_INVALID", "Dataset güvenli tipte olmalıdır.")
    if not isinstance(cache_path, Path):
        raise SweepError("SWEEP_CACHE_PATH_INVALID", "Cache yolu Path olmalıdır.")
    try:
        payload = pickle.dumps(dataset, protocol=pickle.HIGHEST_PROTOCOL)
    except (pickle.PicklingError, TypeError) as error:
        raise SweepError("SWEEP_CACHE_SERIALIZE_INVALID", "Dataset cache'lenemedi.") from error
    try:
        cache_path.write_bytes(payload)
    except OSError as error:
        raise SweepError("SWEEP_CACHE_WRITE_INVALID", "Cache dosyasına yazılamadı.") from error


def init_sweep_worker(cache_path: str) -> None:
    """Load the bar cache once per worker process (pool initializer)."""

    global _SWEEP_DATASET
    try:
        with open(cache_path, "rb") as handle:
            dataset = pickle.load(handle)  # noqa: S301 - trusted local cache file
    except (OSError, pickle.UnpicklingError, ValueError) as error:
        raise SweepError("SWEEP_CACHE_READ_INVALID", "Worker cache'i okuyamadı.") from error
    if not isinstance(dataset, HistoricalDatasetInput):
        raise SweepError("SWEEP_DATASET_INVALID", "Cache güvenli tipte değil.")
    _SWEEP_DATASET = dataset


def run_sweep_task(task: dict) -> dict:
    """Run one recipe against the worker-local dataset (top-level, picklable)."""

    if _SWEEP_DATASET is None:
        raise SweepError("SWEEP_WORKER_UNINITIALIZED", "Worker dataset yüklenmeden çalıştı.")
    if not isinstance(task, dict) or set(task) != {"recipe_id", "raw_config"}:
        raise SweepError("SWEEP_TASK_INVALID", "Task {recipe_id, raw_config} olmalıdır.")
    recipe_id = task["recipe_id"]
    if not isinstance(recipe_id, str) or _RECIPE_ID.fullmatch(recipe_id) is None:
        raise SweepError("SWEEP_TASK_INVALID", "recipe_id biçimi geçersiz.")
    return _execute_recipe(recipe_id, _SWEEP_DATASET, task["raw_config"])


def run_parameter_sweep(
    recipes: tuple,
    *,
    base_config: dict,
    dataset: HistoricalDatasetInput | None = None,
    cache_path: Path | None = None,
    max_workers: int = 1,
) -> tuple:
    """Run validated recipes sequentially or across worker processes."""

    if not isinstance(recipes, tuple):
        raise SweepError("SWEEP_RECIPES_INVALID", "Tarifler tuple olmalıdır.")
    if len(recipes) > _MAX_RECIPES:
        raise SweepError("SWEEP_RECIPES_INVALID", "Tarif sayısı sınırı aştı.")
    if not isinstance(base_config, dict):
        raise SweepError("SWEEP_BASE_CONFIG_INVALID", "Base config dict olmalıdır.")
    if type(max_workers) is not int or not 1 <= max_workers <= _MAX_WORKERS:
        raise SweepError("SWEEP_WORKERS_INVALID", "Worker sayısı 1-16 olmalıdır.")
    tasks = []
    for task in recipes:
        recipe_id, overrides = _prepare_recipe(task)
        raw_config = dict(base_config)
        raw_config.update(overrides)
        tasks.append({"recipe_id": recipe_id, "raw_config": raw_config})
    if not tasks:
        return ()
    if max_workers == 1:
        if dataset is None:
            raise SweepError("SWEEP_DATASET_INVALID", "Sıralı koşu dataset ister.")
        _require_dataset(dataset)
        return tuple(_execute_recipe(task["recipe_id"], dataset, task["raw_config"]) for task in tasks)
    if cache_path is None:
        raise SweepError("SWEEP_CACHE_PATH_INVALID", "Paralel koşu cache_path ister.")
    if dataset is not None:
        write_sweep_cache(dataset, cache_path)
    elif not (isinstance(cache_path, Path) and cache_path.exists()):
        raise SweepError("SWEEP_CACHE_PATH_INVALID", "Cache dosyası bulunamadı.")
    results: list = [None] * len(tasks)
    with ProcessPoolExecutor(
        max_workers=max_workers,
        initializer=init_sweep_worker,
        initargs=(str(cache_path),),
    ) as pool:
        futures = [pool.submit(run_sweep_task, task) for task in tasks]
        for index, future in enumerate(futures):
            try:
                results[index] = future.result()
            except SweepError as error:
                raise SweepError(
                    error.code, f"Tarif başarısız: {tasks[index]['recipe_id']}: {error}"
                ) from error
            except Exception as error:
                raise SweepError(
                    "SWEEP_TASK_FAILED", f"Tarif başarısız: {tasks[index]['recipe_id']}: {error}"
                ) from error
    return tuple(results)


def _prepare_recipe(task: object) -> tuple:
    if not isinstance(task, dict) or set(task) != {"recipe_id", "overrides"}:
        raise SweepError("SWEEP_RECIPE_INVALID", "Tarif {recipe_id, overrides} olmalıdır.")
    recipe_id = task["recipe_id"]
    overrides = task["overrides"]
    if not isinstance(recipe_id, str) or _RECIPE_ID.fullmatch(recipe_id) is None:
        raise SweepError("SWEEP_RECIPE_INVALID", "recipe_id biçimi geçersiz.")
    if not isinstance(overrides, dict):
        raise SweepError("SWEEP_RECIPE_INVALID", "overrides dict olmalıdır.")
    unknown = set(overrides) - _SWEEPABLE
    if unknown:
        raise SweepError(
            "SWEEP_OVERRIDE_INVALID", f"Sweep edilemeyen alan: {sorted(unknown)[0]}."
        )
    for name, value in overrides.items():
        if name == "safety_count":
            if type(value) is not int:
                raise SweepError("SWEEP_OVERRIDE_INVALID", "safety_count integer olmalıdır.")
        elif not isinstance(value, str):
            raise SweepError("SWEEP_OVERRIDE_INVALID", f"{name} string olmalıdır.")
    return recipe_id, dict(overrides)


def _execute_recipe(recipe_id: str, dataset: HistoricalDatasetInput, raw_config: object) -> dict:
    if not isinstance(raw_config, dict):
        raise SweepError("SWEEP_TASK_FAILED", f"Tarif başarısız: {recipe_id}: raw_config dict değil.")
    try:
        config = Config.parse(raw_config)
        config_hash = hashlib.sha256(canonical_json(raw_config).encode("utf-8")).hexdigest()
        result = simulate_historical_ohlcv(dataset, config, config_hash=config_hash)
    except (TypeError, ValueError) as error:
        raise SweepError("SWEEP_TASK_FAILED", f"Tarif başarısız: {recipe_id}: {error}") from error
    summary = result.summary
    if not isinstance(summary, dict):
        raise SweepError("SWEEP_TASK_FAILED", f"Tarif başarısız: {recipe_id}: özet dict değil.")
    return {
        "recipe_id": recipe_id,
        "config_hash": config_hash,
        "execution_status": result.execution_status,
        "processed_bar_count": result.processed_bar_count,
        "position_status": result.position_status,
        "fee_amount": result.fee_amount,
        "action_count": len(result.actions),
        "summary": dict(summary),
    }


def _require_dataset(dataset: object) -> None:
    if not isinstance(dataset, HistoricalDatasetInput):
        raise SweepError("SWEEP_DATASET_INVALID", "Dataset güvenli tipte olmalıdır.")
