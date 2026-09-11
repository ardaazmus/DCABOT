"""Versioned configuration for one synthetic, long-only deal."""

from dataclasses import dataclass
from fractions import Fraction as Q
import re
from .numbers import number, align
from .math import build_plan


@dataclass(frozen=True)
class Config:
    symbol: str
    base_asset: str
    quote_asset: str
    base_qty: Q
    safety_qty: Q
    safety_count: int
    deviation: Q
    step_multiplier: Q
    volume_multiplier: Q
    tick: Q
    qty_step: Q
    min_qty: Q
    min_notional: Q
    initial_equity: Q
    max_entry_notional: Q
    leverage: Q
    max_drawdown: Q
    minimum_equity: Q
    take_profit: Q
    target_mode: str
    target_quote: Q
    fee_rate: Q
    fee_quantum: Q
    slippage: Q

    @classmethod
    def parse(cls, raw: dict) -> "Config":
        if not isinstance(raw, dict) or set(raw) != set(cls.__dataclass_fields__) | {
            "mode",
            "schema_version",
        }:
            raise ValueError("Config fields must exactly match config/paper.json")
        if (
            raw["mode"] != "offline"
            or type(raw["schema_version"]) is not int
            or raw["schema_version"] != 1
        ):
            raise ValueError("Only offline config schema 1 is supported")
        if (
            raw["quote_asset"] != "USDT"
            or not isinstance(raw["base_asset"], str)
            or not re.fullmatch("[A-Z0-9]{2,12}", raw["base_asset"])
        ):
            raise ValueError("Only explicit BASE/USDT linear instruments are supported")
        if raw["symbol"] != raw["base_asset"] + "USDT":
            raise ValueError("Symbol does not match asset units")
        if raw["target_mode"] not in ("GROSS_PRICE_RETURN", "NET_QUOTE"):
            raise ValueError("Unknown target mode")
        if type(raw["safety_count"]) is not int or not 0 <= raw["safety_count"] <= 50:
            raise ValueError("Safety count must be integer 0..50")
        categorical = {
            "symbol",
            "base_asset",
            "quote_asset",
            "target_mode",
            "safety_count",
        }
        values = {
            k: raw[k] if k in categorical else number(raw[k])
            for k in cls.__dataclass_fields__
        }
        c = cls(**values)
        for name in (
            "base_qty",
            "safety_qty",
            "deviation",
            "step_multiplier",
            "volume_multiplier",
            "tick",
            "qty_step",
            "min_qty",
            "min_notional",
            "initial_equity",
            "max_entry_notional",
            "leverage",
            "max_drawdown",
            "take_profit",
            "fee_quantum",
        ):
            if getattr(c, name) <= 0:
                raise ValueError(f"{name} must be positive")
        if not (
            c.leverage <= 100
            and c.max_drawdown < 1
            and c.deviation < 1
            and c.take_profit < 1
            and 0 <= c.fee_rate < 1
            and 0 <= c.slippage < 1
            and 0 <= c.minimum_equity < c.initial_equity
            and c.target_quote >= 0
        ):
            raise ValueError("Invalid policy range")
        # Executable input grid: at most 12 decimals, input upper bound inherited from number().
        for name in ("tick", "qty_step", "fee_quantum", "base_qty", "safety_qty"):
            if (getattr(c, name) * 10**12).denominator != 1:
                raise ValueError(f"{name} supports at most 12 decimals")
        if (
            align(c.base_qty, c.qty_step, up=False) != c.base_qty
            or c.base_qty < c.min_qty
        ):
            raise ValueError("Base quantity is below minimum or off-grid")
        return c

    def plan(self, anchor: Q):
        plan = build_plan(
            anchor,
            self.safety_qty,
            self.safety_count,
            self.deviation,
            self.step_multiplier,
            self.volume_multiplier,
            self.tick,
            self.qty_step,
        )
        for level in plan:
            self.check_order(level.qty, level.price)
        return plan

    def check_order(self, qty: Q, price: Q) -> None:
        if qty < self.min_qty or price <= 0 or qty * price < self.min_notional:
            raise ValueError("Order below quantity/notional minimum")
        if (
            align(qty, self.qty_step, up=False) != qty
            or align(price, self.tick, up=False) != price
        ):
            raise ValueError("Order is off the instrument grid")
