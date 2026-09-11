"""Pure bootstrap policy: accepts only the documented offline mode."""

from collections.abc import Mapping


def describe_bootstrap(config: Mapping[str, object]) -> dict[str, object]:
    if set(config) != {"mode"}:
        raise ValueError("Config must contain exactly one field: mode")
    if config["mode"] != "offline":
        raise ValueError("Only offline mode is implemented")
    return {
        "mode": "offline",
        "stage": "OFFLINE_CORE",
        "trading_enabled": False,
        "strategy_implemented": True,
    }
