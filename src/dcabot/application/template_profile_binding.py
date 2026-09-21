"""Bind inert strategy templates to registered historical profiles.

Ownership split (explicit): a template may only override STRATEGY params
(sizing, ladder, targets). Venue grid (tick/qty_step/minima), execution
model (fee/slippage), risk policy (equity/leverage/drawdown), instrument
identity, and schema stay owned by the profile. A shared template can
therefore never silently change risk limits or the venue grid.

Binding validates each override in isolation. Full cross-field consistency
(off-grid, minima) is checked at materialization, when overrides merge with
the profile config through ``Config.parse``. Binding creates no run, no
candidate, no order, and no fill.
"""

from dataclasses import dataclass
import hashlib
import json

from dcabot.application.historical_profiles import (
    HistoricalProfileError,
    get_historical_profile,
)
from dcabot.application.strategy_template import StrategyTemplate
from dcabot.application.template_activation_gate import assess_template_activation
from dcabot.domain.numbers import number


_SCHEMA = "template-binding-v1"
_NUMERIC_POSITIVE = frozenset(
    {
        "base_qty",
        "safety_qty",
        "step_multiplier",
        "volume_multiplier",
        "max_entry_notional",
    }
)
_NUMERIC_FRACTION = frozenset({"deviation", "take_profit"})
_NUMERIC_NONNEGATIVE = frozenset({"target_quote"})
_QTY_GRID = frozenset({"base_qty", "safety_qty"})
BINDABLE_PARAMS = frozenset(
    _NUMERIC_POSITIVE
    | _NUMERIC_FRACTION
    | _NUMERIC_NONNEGATIVE
    | {"safety_count", "target_mode"}
)
_TARGET_MODES = frozenset({"GROSS_PRICE_RETURN", "NET_QUOTE"})


class TemplateBindingError(ValueError):
    """Raised when a template cannot bind to a profile safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class TemplateBinding:
    """Immutable approved binding; still not a run, candidate, or order."""

    binding_id: str
    schema_version: str
    status: str
    template_id: str
    template_sha256: str
    profile_id: str
    params: tuple[tuple[str, object], ...]
    binding_time_us: int


def bind_template_to_profile(
    *,
    template: StrategyTemplate,
    profile_id: str,
    allowed_capabilities: tuple[str, ...],
    approval: str,
    binding_time_us: int,
) -> TemplateBinding:
    """Approve one template against one registered profile with checked params."""

    if not isinstance(template, StrategyTemplate):
        raise TemplateBindingError(
            "TEMPLATE_BINDING_TEMPLATE_INVALID", "Strategy template geçersiz."
        )
    if type(binding_time_us) is not int or binding_time_us < 0:
        raise TemplateBindingError(
            "TEMPLATE_BINDING_TIME_INVALID",
            "Binding zamanı sıfır veya pozitif integer olmalıdır.",
        )
    try:
        decision = assess_template_activation(
            template,
            allowed_capabilities=allowed_capabilities,
            approval=approval,
        )
    except ValueError as error:
        raise TemplateBindingError(
            "TEMPLATE_BINDING_APPROVAL_INVALID",
            "Onay/kapabilite girdisi geçersiz.",
        ) from error
    if decision.status != "READY_FOR_ACTIVATION":
        raise TemplateBindingError(
            "TEMPLATE_BINDING_NOT_READY",
            f"Template aktive edilebilir durumda değil: {decision.status}.",
        )
    try:
        profile = get_historical_profile(profile_id)
    except HistoricalProfileError as error:
        raise TemplateBindingError(
            "TEMPLATE_BINDING_PROFILE_UNKNOWN",
            "Historical profile katalogda bulunamadı.",
        ) from error

    try:
        payload = json.loads(template.payload_json)
    except (TypeError, ValueError) as error:
        raise TemplateBindingError(
            "TEMPLATE_BINDING_PAYLOAD_INVALID", "Template payload okunamadı."
        ) from error
    if not isinstance(payload, dict) or not payload:
        raise TemplateBindingError(
            "TEMPLATE_BINDING_EMPTY", "Bağlanacak parametre yok."
        )
    checked: dict[str, object] = {}
    for key in sorted(payload):
        if key not in BINDABLE_PARAMS:
            raise TemplateBindingError(
                "TEMPLATE_BINDING_PARAM_UNKNOWN",
                f"Parametre bağlanamaz (profil sahipliğinde): {key}.",
            )
        checked[key] = _checked_value(key, payload[key])

    canonical = json.dumps(
        {
            "binding_time_us": binding_time_us,
            "params": [[key, checked[key]] for key in sorted(checked)],
            "profile_id": profile.profile_id,
            "schema": _SCHEMA,
            "template_id": template.template_id,
            "template_sha256": template.payload_sha256,
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return TemplateBinding(
        binding_id=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        schema_version=_SCHEMA,
        status="BOUND",
        template_id=template.template_id,
        template_sha256=template.payload_sha256,
        profile_id=profile.profile_id,
        params=tuple((key, checked[key]) for key in sorted(checked)),
        binding_time_us=binding_time_us,
    )


def _checked_value(key: str, value: object) -> object:
    if key == "safety_count":
        if type(value) is not int or not 0 <= value <= 50:
            raise TemplateBindingError(
                "TEMPLATE_BINDING_PARAM_INVALID",
                "safety_count 0 ile 50 arasında integer olmalıdır.",
            )
        return value
    if key == "target_mode":
        if value not in _TARGET_MODES:
            raise TemplateBindingError(
                "TEMPLATE_BINDING_PARAM_INVALID",
                "target_mode bilinmiyor.",
            )
        return value
    if not isinstance(value, str):
        raise TemplateBindingError(
            "TEMPLATE_BINDING_PARAM_INVALID",
            f"{key} decimal string olmalıdır.",
        )
    try:
        parsed = number(value)
    except ValueError as error:
        raise TemplateBindingError(
            "TEMPLATE_BINDING_PARAM_INVALID",
            f"{key} decimal string olmalıdır.",
        ) from error
    if key in _NUMERIC_POSITIVE and parsed <= 0:
        raise TemplateBindingError(
            "TEMPLATE_BINDING_PARAM_INVALID", f"{key} pozitif olmalıdır."
        )
    if key in _NUMERIC_FRACTION and not 0 < parsed < 1:
        raise TemplateBindingError(
            "TEMPLATE_BINDING_PARAM_INVALID", f"{key} 0 ile 1 arasında olmalıdır."
        )
    if key in _NUMERIC_NONNEGATIVE and parsed < 0:
        raise TemplateBindingError(
            "TEMPLATE_BINDING_PARAM_INVALID", f"{key} negatif olamaz."
        )
    if key in _QTY_GRID and (parsed * 10**12).denominator != 1:
        raise TemplateBindingError(
            "TEMPLATE_BINDING_PARAM_INVALID", f"{key} en fazla 12 ondalık taşıyabilir."
        )
    return value
