"""Capability and approval gate that never activates a strategy itself."""

from dataclasses import dataclass
import re

from dcabot.application.strategy_template import StrategyTemplate


_IDENTIFIER = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)
_APPROVALS = frozenset({"PENDING", "APPROVED"})


class TemplateActivationError(ValueError):
    """Raised when a template activation gate input is invalid."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class TemplateActivationDecision:
    """Read-only activation decision; it contains no activation operation."""

    template_id: str
    status: str
    declared_capabilities: tuple[str, ...]
    unsupported_capabilities: tuple[str, ...]


def assess_template_activation(
    template: StrategyTemplate,
    *,
    allowed_capabilities: tuple[str, ...],
    approval: str,
) -> TemplateActivationDecision:
    """Check capabilities and approval without creating an active strategy.

    ``APPROVED`` means that a later, separately owned activation transition
    may proceed. It does not itself create a candidate, order, reserve, or
    fill.
    """

    if not isinstance(template, StrategyTemplate):
        raise TemplateActivationError(
            "TEMPLATE_ACTIVATION_INPUT_INVALID", "Strategy template geçersiz."
        )
    if not isinstance(approval, str) or approval not in _APPROVALS:
        raise TemplateActivationError(
            "TEMPLATE_APPROVAL_INVALID",
            "Approval yalnız PENDING veya APPROVED olabilir.",
        )
    if not isinstance(allowed_capabilities, tuple):
        raise TemplateActivationError(
            "TEMPLATE_ALLOWED_CAPABILITIES_INVALID",
            "Allowed capabilities tuple olmalıdır.",
        )
    for capability in allowed_capabilities:
        if not isinstance(capability, str) or _IDENTIFIER.fullmatch(capability) is None:
            raise TemplateActivationError(
                "TEMPLATE_ALLOWED_CAPABILITY_INVALID",
                "Allowed capability identifier olmalıdır.",
            )
    if len(set(allowed_capabilities)) != len(allowed_capabilities):
        raise TemplateActivationError(
            "TEMPLATE_ALLOWED_CAPABILITY_DUPLICATE",
            "Allowed capability tekrar edemez.",
        )

    unsupported = tuple(
        capability
        for capability in template.declared_capabilities
        if capability not in allowed_capabilities
    )
    if unsupported:
        status = "CAPABILITY_UNSUPPORTED"
    elif approval == "PENDING":
        status = "AWAITING_APPROVAL"
    else:
        status = "READY_FOR_ACTIVATION"
    return TemplateActivationDecision(
        template_id=template.template_id,
        status=status,
        declared_capabilities=template.declared_capabilities,
        unsupported_capabilities=unsupported,
    )
