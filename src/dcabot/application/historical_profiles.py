"""Explicit, immutable config profiles for bounded historical runs."""

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Final

from dcabot.domain.config import Config


PROFILE_ID_PATTERN: Final = re.compile(r"[a-z0-9](?:[a-z0-9_-]{0,126}[a-z0-9])?\Z", re.ASCII)


class HistoricalProfileError(ValueError):
    """Raised when a requested historical profile is unavailable or invalid."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class HistoricalProfile:
    """A named config binding with explicit offline-demo provenance."""

    profile_id: str
    profile_version: str
    label: str
    config_filename: str
    expected_dataset_id: str | None
    venue_filter_provenance: str
    historical_filter_claim: bool
    anchor_source: str
    simulation_model: str = "historical_ohlcv_v1"
    slice_qty: str | None = None


HISTORICAL_PROFILES: Final = (
    HistoricalProfile(
        profile_id="paper",
        profile_version="1",
        label="Paper config (v1)",
        config_filename="paper.json",
        expected_dataset_id=None,
        venue_filter_provenance="project_fixture",
        historical_filter_claim=False,
        anchor_source="dataset_first_bar_open",
    ),
    HistoricalProfile(
        profile_id="historical_demo_btcusdt_1h_v1",
        profile_version="1",
        label="Historical demo — BTCUSDT 1h (v1)",
        config_filename="historical_demo_btcusdt_1h_v1.json",
        expected_dataset_id="binance-spot-klines-v1-btcusdt-1h-2025-01-01",
        venue_filter_provenance="project_fixture",
        historical_filter_claim=False,
        anchor_source="dataset_first_bar_open",
    ),
)
HISTORICAL_OPT_IN_PROFILES: Final = (
    HistoricalProfile(
        profile_id="historical_demo_btcusdt_1h_partial_fixed_v1",
        profile_version="1",
        label="Historical demo — BTCUSDT 1h partial fixed slice (v1)",
        config_filename="historical_demo_btcusdt_1h_v1.json",
        expected_dataset_id="binance-spot-klines-v1-btcusdt-1h-2025-01-01",
        venue_filter_provenance="project_fixture",
        historical_filter_claim=False,
        anchor_source="dataset_first_bar_open",
        simulation_model="historical_ohlcv_partial_fixed_v1",
        slice_qty="0.001",
    ),
)
_PROFILE_BY_ID: Final = {
    profile.profile_id: profile for profile in (*HISTORICAL_PROFILES, *HISTORICAL_OPT_IN_PROFILES)
}


def list_historical_profiles() -> tuple[HistoricalProfile, ...]:
    """Return the bounded deterministic profile registry."""

    return (*HISTORICAL_PROFILES, *HISTORICAL_OPT_IN_PROFILES)


def get_historical_profile(profile_id: str) -> HistoricalProfile:
    """Resolve only an explicitly registered profile ID."""

    if not isinstance(profile_id, str) or PROFILE_ID_PATTERN.fullmatch(profile_id) is None:
        raise HistoricalProfileError("PROFILE_ID_INVALID", "Historical profile kimliği geçersiz.")
    profile = _PROFILE_BY_ID.get(profile_id)
    if profile is None:
        raise HistoricalProfileError("PROFILE_NOT_FOUND", "Historical profile katalogda bulunamadı.")
    return profile


def load_historical_profile_config(root: Path, profile_id: str) -> tuple[HistoricalProfile, dict[str, object]]:
    """Load and validate one registered profile without allowing arbitrary paths."""

    profile = get_historical_profile(profile_id)
    config_path = (root / "config" / profile.config_filename).resolve()
    config_root = (root / "config").resolve()
    if config_path.parent != config_root:
        raise HistoricalProfileError("PROFILE_PATH_INVALID", "Historical profile yolu güvenli değil.")
    try:
        with config_path.open(encoding="utf-8") as handle:
            raw_config = json.load(handle)
        Config.parse(raw_config)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise HistoricalProfileError("PROFILE_CONFIG_INVALID", "Historical profile config doğrulanamadı.") from exc
    return profile, raw_config
