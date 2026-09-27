"""Versioned configuration for one synthetic, long-only deal."""

from dataclasses import dataclass
from fractions import Fraction as Q
import re
from .numbers import number, align
from .math import Direction, build_plan


# Faz G1-kalan/a: entry-gate cooldown cap -- at most a year of silence.
MAX_COOLDOWN_SECONDS = 31_536_000


@dataclass(frozen=True, slots=True)
class TakeProfitLevel:
    """Faz 17 H.1 (RG-10): one rung of a partial-take-profit ladder.
    `weight` is a fraction of the LADDER-START position quantity (captured
    once, when the first level fires) -- NEVER a fraction of the remaining
    position, per the research's documented bug class (independent
    remaining-percent math leaves ~31.6% of the position permanently open
    after 4x25% levels). The engine additionally forces the LAST configured
    level to close the true remainder regardless of its nominal `weight`."""

    weight: Q
    target_percent: Q


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
    take_profit: Q | None
    target_mode: str
    target_quote: Q
    fee_rate: Q
    fee_quantum: Q
    slippage: Q
    margin_mode: str
    direction: str = "LONG"
    max_active_safety_orders: int | None = None
    base_order_type: str = "LIMIT"
    safety_order_type: str = "LIMIT"
    exit_order_type: str = "LIMIT"
    stop_order_type: str = "LIMIT"
    max_adverse_slippage_bps: Q | None = None
    slippage_reference: str = "MARK"
    take_profit_ladder: tuple[TakeProfitLevel, ...] | None = None
    stop_loss_rate: Q | None = None
    stop_loss_confirmation_bars: int | None = None
    trailing_take_profit_rate: Q | None = None
    max_deal_duration_seconds: int | None = None
    max_deal_duration_action: str | None = None
    profit_asset: str | None = None
    safety_sizing: str = "BASE"
    base_sizing: str = "BASE"
    cooldown_seconds: int = 0
    min_entry_price: Q | None = None
    max_entry_price: Q | None = None

    @classmethod
    def parse(cls, raw: dict) -> "Config":
        if not isinstance(raw, dict):
            raise ValueError("Config fields must exactly match config/paper.json")
        # Faz 17 C.1/G.3: `direction` and `max_active_safety_orders` are new;
        # absence defaults them (LONG / None) so every existing config
        # file/hash stays byte-for-byte unchanged. A local copy is used so
        # the caller's dict (often reused for canonical hashing elsewhere,
        # e.g. template_materialization) is never mutated.
        raw = dict(raw)
        raw.setdefault("direction", "LONG")
        raw.setdefault("max_active_safety_orders", None)
        raw.setdefault("base_order_type", "LIMIT")
        raw.setdefault("safety_order_type", "LIMIT")
        raw.setdefault("exit_order_type", "LIMIT")
        raw.setdefault("stop_order_type", "LIMIT")
        raw.setdefault("max_adverse_slippage_bps", None)
        raw.setdefault("slippage_reference", "MARK")
        raw.setdefault("take_profit_ladder", None)
        raw.setdefault("stop_loss_rate", None)
        raw.setdefault("stop_loss_confirmation_bars", None)
        raw.setdefault("trailing_take_profit_rate", None)
        raw.setdefault("max_deal_duration_seconds", None)
        raw.setdefault("max_deal_duration_action", None)
        raw.setdefault("profit_asset", None)
        raw.setdefault("safety_sizing", "BASE")
        raw.setdefault("base_sizing", "BASE")
        raw.setdefault("cooldown_seconds", 0)
        raw.setdefault("min_entry_price", None)
        raw.setdefault("max_entry_price", None)
        if set(raw) != set(cls.__dataclass_fields__) | {
            "mode",
            "schema_version",
        }:
            raise ValueError("Config fields must exactly match config/paper.json")
        if raw["direction"] not in ("LONG", "SHORT"):
            raise ValueError("direction must be LONG or SHORT")
        # Faz W: QUOTE reads safety_qty as the first safety order's quote
        # amount (3Commas/Bitsgap/Pionex convention); BASE is the unchanged
        # default, so existing config files and hashes stay byte-identical.
        if raw["safety_sizing"] not in ("BASE", "QUOTE"):
            raise ValueError("safety_sizing must be BASE or QUOTE")
        # Faz W: QUOTE reads base_qty as the base order's quote amount; the
        # quantity is derived at the order's own price (base_order_qty).
        if raw["base_sizing"] not in ("BASE", "QUOTE"):
            raise ValueError("base_sizing must be BASE or QUOTE")
        # Faz 17 G.1 (RG-06): margin_mode is mandatory, no default, no
        # silent fall-through to the venue's own default -- unlike every
        # other field added this phase. Absence is already rejected by the
        # exact-field-match check above (no setdefault call exists for it).
        if raw.get("margin_mode") not in ("ISOLATED", "CROSS"):
            raise ValueError("margin_mode must be ISOLATED or CROSS")
        max_active_so = raw["max_active_safety_orders"]
        if max_active_so is not None and type(max_active_so) is not int:
            raise ValueError("max_active_safety_orders must be an integer or null")
        # Faz 17 G.2 (RG-07): Market/Limit per role + a single live adverse-
        # slippage bound. `slippage_reference` only supports MARK today (the
        # engine has no separate LAST/MID feed) -- LAST/MID are rejected
        # fail-closed rather than silently treated as MARK.
        order_type_fields = (
            "base_order_type",
            "safety_order_type",
            "exit_order_type",
            "stop_order_type",
        )
        for field_name in order_type_fields:
            if raw[field_name] not in ("MARKET", "LIMIT"):
                raise ValueError(f"{field_name} must be MARKET or LIMIT")
        if raw["slippage_reference"] != "MARK":
            raise ValueError("slippage_reference only supports MARK for now")
        any_market_order_type = any(raw[f] == "MARKET" for f in order_type_fields)
        max_adverse_bps = raw["max_adverse_slippage_bps"]
        if max_adverse_bps is not None:
            if not any_market_order_type:
                raise ValueError(
                    "max_adverse_slippage_bps must be null unless an order_type is MARKET"
                )
            if not isinstance(max_adverse_bps, str):
                raise ValueError("max_adverse_slippage_bps must be a decimal string or null")
            max_adverse_bps = number(max_adverse_bps)
            if not 0 < max_adverse_bps < 10000:
                raise ValueError(
                    "max_adverse_slippage_bps must be within 0..10000 (bps), exclusive"
                )
            raw["max_adverse_slippage_bps"] = max_adverse_bps
        elif any_market_order_type:
            raise ValueError(
                "max_adverse_slippage_bps is required when an order_type is MARKET"
            )
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
        # Faz 17 I.1 (RG-12): profit currency is EXACTLY one of the two
        # assets already in play (quote or base) -- research (konu 12/12,
        # cross-checked against 3Commas/Pionex/Bitsgap/Freqtrade) found none
        # of them offer "convert profit to an arbitrary third coin"; doing
        # so would require an extra live conversion trade this engine does
        # not (and should not, without a separate live-trading approval)
        # execute. `None` defaults to quote_asset -- today's implicit,
        # unchanged behavior (every exit already sells fully to quote).
        profit_asset_raw = raw["profit_asset"]
        if profit_asset_raw is not None and profit_asset_raw not in (raw["base_asset"], raw["quote_asset"]):
            raise ValueError("profit_asset must be null, base_asset, or quote_asset")
        if raw["target_mode"] not in ("GROSS_PRICE_RETURN", "NET_QUOTE"):
            raise ValueError("Unknown target mode")
        # Faz 17 H.1 (RG-10): partial-TP ladder is additive and OFF by
        # default (null). NET_QUOTE's cost-recovery target is LONG-only and
        # single-shot by design (Faz 17 C.3 scope); combining it with a
        # multi-level ladder is a separate, harder economic-design question
        # not addressed here -- fail closed instead of guessing.
        ladder_raw = raw["take_profit_ladder"]
        if ladder_raw is not None:
            if raw["target_mode"] == "NET_QUOTE":
                raise ValueError("take_profit_ladder does not yet support NET_QUOTE target_mode")
            if not isinstance(ladder_raw, list) or len(ladder_raw) < 2:
                raise ValueError("take_profit_ladder must be a list of at least 2 levels, or null")
            levels: list[TakeProfitLevel] = []
            weight_sum = Q(0)
            previous_target: Q | None = None
            for item in ladder_raw:
                if (
                    not isinstance(item, list)
                    or len(item) != 2
                    or not all(isinstance(x, str) for x in item)
                ):
                    raise ValueError("Each take_profit_ladder level must be a [weight, target_percent] string pair")
                weight = number(item[0])
                target_percent = number(item[1])
                if not 0 < weight <= 1:
                    raise ValueError("take_profit_ladder weight must be within 0..1 (exclusive of 0)")
                if not 0 < target_percent < 1:
                    raise ValueError("take_profit_ladder target_percent must be within 0..1 (exclusive)")
                if previous_target is not None and target_percent <= previous_target:
                    raise ValueError("take_profit_ladder target_percent must be strictly increasing")
                previous_target = target_percent
                levels.append(TakeProfitLevel(weight=weight, target_percent=target_percent))
                weight_sum += weight
            if weight_sum != 1:
                raise ValueError("take_profit_ladder weights must sum to exactly 1")
            if profit_asset_raw is not None and profit_asset_raw == raw["base_asset"]:
                # Faz 17 I.1: base-asset profit retention (cost-recovery
                # sell + WITHDRAW_PROFIT) is designed only for the single,
                # non-laddered EXIT path -- composing it with a multi-level
                # ladder is a separate, harder design question, not solved
                # here. Fail closed instead of guessing a per-level split.
                raise ValueError("take_profit_ladder does not yet support a base_asset profit_asset")
            raw["take_profit_ladder"] = tuple(levels)
        # Faz 17 H.2 (RG-11): price-level stop-loss with bar-close
        # confirmation -- OFF by default (both null). Research (konu 11/12)
        # found two incompatible confirmation models (single delayed
        # re-check vs. continuous dwell) and warned that a seconds-based
        # mode cannot be honestly simulated against OHLC bar data -- so only
        # a bar-count confirmation is accepted; there is no
        # "continuous_seconds" mode to silently misrepresent in backtests.
        sl_rate_raw = raw["stop_loss_rate"]
        sl_bars = raw["stop_loss_confirmation_bars"]
        if sl_rate_raw is not None:
            if not isinstance(sl_rate_raw, str):
                raise ValueError("stop_loss_rate must be a decimal string or null")
            sl_rate = number(sl_rate_raw)
            if not 0 < sl_rate < 1:
                raise ValueError("stop_loss_rate must be within 0..1 (exclusive)")
            raw["stop_loss_rate"] = sl_rate
            if type(sl_bars) is not int or sl_bars < 1:
                raise ValueError(
                    "stop_loss_confirmation_bars must be a positive integer when stop_loss_rate is set"
                )
        elif sl_bars is not None:
            raise ValueError("stop_loss_confirmation_bars must be null unless stop_loss_rate is set")
        # F09a: trailing take-profit -- a fraction in 0..1 (exclusive),
        # OFF by default. It needs a take-profit activation target; a
        # null take_profit (combo bots) with trailing fails closed here
        # so the ratchet can never silently stay inactive.
        trail_raw = raw["trailing_take_profit_rate"]
        if trail_raw is not None:
            if not isinstance(trail_raw, str):
                raise ValueError("trailing_take_profit_rate must be a decimal string or null")
            trail_rate = number(trail_raw)
            if not 0 < trail_rate < 1:
                raise ValueError("trailing_take_profit_rate must be within 0..1 (exclusive)")
            raw["trailing_take_profit_rate"] = trail_rate
            if raw["take_profit"] is None:
                raise ValueError("trailing_take_profit_rate needs a take_profit activation target")
        # G4-a: null suppresses the engine-level take-profit exit (combo
        # bots close on the runner-level combined target instead). The key
        # stays mandatory; only null becomes a legal value.
        tp_raw = raw["take_profit"]
        if tp_raw is not None:
            raw["take_profit"] = number(tp_raw)
        # Faz 17 H.2 (RG-11): Max Deal Duration -- verified sector-real only
        # for 3Commas ("Trade maximum hold period"); no single universal
        # action exists (Pionex/Bitsgap have no equivalent contract), so the
        # action is an explicit, required enum whenever the duration itself
        # is set, never a silently-assumed default.
        duration_raw = raw["max_deal_duration_seconds"]
        action_raw = raw["max_deal_duration_action"]
        if duration_raw is not None:
            if type(duration_raw) is not int or duration_raw < 1:
                raise ValueError("max_deal_duration_seconds must be a positive integer or null")
            if action_raw not in ("FORCE_CLOSE", "STOP_NEW_SAFETY_ORDERS", "WARN_ONLY", "FREEZE"):
                raise ValueError(
                    "max_deal_duration_action must be FORCE_CLOSE/STOP_NEW_SAFETY_ORDERS/"
                    "WARN_ONLY/FREEZE when max_deal_duration_seconds is set"
                )
        elif action_raw is not None:
            raise ValueError("max_deal_duration_action must be null unless max_deal_duration_seconds is set")
        # Faz G1-kalan/a: entry gates -- a cooldown after each deal close
        # and an optional entry price band. Both default open (0/None) so
        # existing configs and hashes stay byte-identical.
        cooldown_raw = raw["cooldown_seconds"]
        if type(cooldown_raw) is not int or not 0 <= cooldown_raw <= MAX_COOLDOWN_SECONDS:
            raise ValueError("cooldown_seconds must be an integer within 0..31536000")
        for name in ("min_entry_price", "max_entry_price"):
            price_raw = raw[name]
            if price_raw is None:
                continue
            if not isinstance(price_raw, str):
                raise ValueError(f"{name} must be a decimal string or null")
            try:
                price = number(price_raw)
            except ValueError as exc:
                raise ValueError(f"{name} must be a decimal string or null") from exc
            if price <= 0:
                raise ValueError(f"{name} must be positive")
            raw[name] = price
        if (
            raw["min_entry_price"] is not None
            and raw["max_entry_price"] is not None
            and raw["min_entry_price"] > raw["max_entry_price"]
        ):
            raise ValueError("min_entry_price must not exceed max_entry_price")
        if type(raw["safety_count"]) is not int or not 0 <= raw["safety_count"] <= 50:
            raise ValueError("Safety count must be integer 0..50")
        if raw["safety_count"] == 0:
            if max_active_so not in (None, 0):
                raise ValueError(
                    "max_active_safety_orders must be null or 0 when safety_count is 0"
                )
        elif max_active_so is not None and not 1 <= max_active_so <= raw["safety_count"]:
            # No clamping: an out-of-range value is a config error, not a
            # silent adjustment (Faz 17 G.3 brief).
            raise ValueError(
                "max_active_safety_orders must be null or within 1..safety_count"
            )
        categorical = {
            "symbol",
            "base_asset",
            "quote_asset",
            "target_mode",
            "safety_count",
            "margin_mode",
            "direction",
            "max_active_safety_orders",
            "base_order_type",
            "safety_order_type",
            "exit_order_type",
            "stop_order_type",
            "slippage_reference",
            "max_adverse_slippage_bps",
            "take_profit_ladder",
            "stop_loss_rate",
            "trailing_take_profit_rate",
            "take_profit",
            "stop_loss_confirmation_bars",
            "max_deal_duration_seconds",
            "max_deal_duration_action",
            "profit_asset",
            "safety_sizing",
            "base_sizing",
            "cooldown_seconds",
            "min_entry_price",
            "max_entry_price",
        }
        values = {
            k: raw[k] if k in categorical else number(raw[k])
            for k in cls.__dataclass_fields__
        }
        c = cls(**values)
        if c.take_profit is not None and c.take_profit <= 0:
            raise ValueError("take_profit must be positive")
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
            "fee_quantum",
        ):
            if getattr(c, name) <= 0:
                raise ValueError(f"{name} must be positive")
        if not (
            c.leverage <= 100
            and c.max_drawdown < 1
            and c.deviation < 1
            and (c.take_profit is None or c.take_profit < 1)
            and 0 <= c.fee_rate < 1
            and 0 <= c.slippage < 1
            and 0 <= c.minimum_equity < c.initial_equity
            and c.target_quote >= 0
        ):
            raise ValueError("Invalid policy range")
        if c.direction == "SHORT" and c.target_mode == "NET_QUOTE":
            # Faz 17 C.3 scope: NET_QUOTE's cost-recovery formula
            # (net_take_profit) is derived LONG-only; giving it a correct
            # SHORT formula is a separate economic-design decision, not
            # implemented here. Fail closed instead of computing a silently
            # wrong number.
            raise ValueError("SHORT direction does not yet support NET_QUOTE target_mode")
        # Executable input grid: at most 12 decimals, input upper bound inherited from number().
        for name in ("tick", "qty_step", "fee_quantum", "base_qty", "safety_qty"):
            if (getattr(c, name) * 10**12).denominator != 1:
                raise ValueError(f"{name} supports at most 12 decimals")
        if c.base_sizing == "BASE" and (
            align(c.base_qty, c.qty_step, up=False) != c.base_qty
            or c.base_qty < c.min_qty
        ):
            raise ValueError("Base quantity is below minimum or off-grid")
        return c

    def base_order_qty(self, price: Q) -> Q:
        """Base order quantity at `price`: the configured quantity, or under
        QUOTE sizing the quote amount divided by price, floored to qty_step."""
        if self.base_sizing == "BASE":
            return self.base_qty
        if price <= 0:
            raise ValueError("Base order price must be positive")
        return align(self.base_qty / price, self.qty_step, up=False)

    @property
    def direction_enum(self) -> Direction:
        return Direction[self.direction]

    @property
    def effective_max_active_safety_orders(self) -> int:
        """Faz 17 G.3: `None` means "unlimited within the ladder", i.e. the
        pre-existing behavior (every safety level may be active), which is
        exactly `safety_count`."""
        return self.safety_count if self.max_active_safety_orders is None else self.max_active_safety_orders

    @property
    def effective_profit_asset(self) -> str:
        """Faz 17 I.1: `None` means "quote" -- today's implicit, unchanged
        behavior (every exit already sells fully to quote)."""
        return self.quote_asset if self.profit_asset is None else self.profit_asset

    def order_type_for_role(self, role: str) -> str:
        """Faz 17 G.2: order_type is configured per role, not globally."""
        if role == "BASE":
            return self.base_order_type
        if role == "EXIT" or (isinstance(role, str) and role.startswith("EXIT:")):
            return self.exit_order_type
        if role == "STOP":
            return self.stop_order_type
        return self.safety_order_type

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
            direction=self.direction_enum,
            sizing=self.safety_sizing,
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
