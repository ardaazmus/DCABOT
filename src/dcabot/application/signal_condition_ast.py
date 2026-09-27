"""Faz 17 G.4 (RG-09): boolean condition AST with three-valued logic.

Research (konu 9/12, M/F/B PASS): 3Commas' native multi-indicator DCA
builder supports only AND -- OR is available exclusively via external
TradingView Pine/webhook, not the native builder. This AST's `Any` node
(OR) is therefore a genuine capability beyond 3Commas' native builder, not
a copy of it.

Three-valued logic (`TRUE`/`FALSE`/`UNKNOWN`) generalizes this codebase's
established "UNKNOWN != SAFE" fail-closed principle into condition
evaluation: a condition that cannot be evaluated (insufficient history, a
missing cross point) is UNKNOWN, not assumed FALSE. `AND(TRUE, UNKNOWN)` is
UNKNOWN (a firm veto still vetoes; an unresolved condition never manufactures
a firm answer). An action fires only on a definite `TRUE` -- `FALSE` and
`UNKNOWN` both withhold action, exactly like the domain's existing
DENY-on-uncertainty gates (RG-05).

Nodes are pure, immutable data (dataclasses); `evaluate()` is a pure
function over them. Nothing here computes indicator values -- callers
supply already-evaluated leaf conditions and (for cross_up/cross_down) the
two aligned series to compare.
"""

from dataclasses import dataclass
from typing import Literal, Union

TriState = Literal["TRUE", "FALSE", "UNKNOWN"]


class SignalConditionError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class Condition:
    """A leaf: an already-evaluated tri-state fact (e.g. "RSI < 30")."""

    value: TriState


@dataclass(frozen=True, slots=True)
class CrossUp:
    """TRUE at the first index where `a` moves from <=b to >b. UNKNOWN if
    either series is missing a value (None) at either of the two points
    compared -- a cross can never be inferred from incomplete data."""

    series_a: tuple[object | None, ...]
    series_b: tuple[object | None, ...]
    index: int


@dataclass(frozen=True, slots=True)
class CrossDown:
    series_a: tuple[object | None, ...]
    series_b: tuple[object | None, ...]
    index: int


@dataclass(frozen=True, slots=True)
class All:
    """AND over children (Kleene): FALSE if any child is FALSE; else
    UNKNOWN if any child is UNKNOWN; else TRUE. An empty child tuple is a
    caller error, not a vacuous TRUE."""

    children: tuple["Node", ...]


@dataclass(frozen=True, slots=True)
class Any_:
    """OR over children (Kleene): TRUE if any child is TRUE; else UNKNOWN
    if any child is UNKNOWN; else FALSE. An empty child tuple is a caller
    error, not a vacuous FALSE."""

    children: tuple["Node", ...]


@dataclass(frozen=True, slots=True)
class Not:
    child: "Node"


Node = Union[Condition, CrossUp, CrossDown, All, Any_, Not]


def _cross(series_a: tuple, series_b: tuple, index: int, *, direction: str) -> TriState:
    if len(series_a) != len(series_b):
        raise SignalConditionError(
            "SIGNAL_CROSS_LENGTH_MISMATCH", "İki seri aynı uzunlukta olmalıdır."
        )
    if index < 1 or index >= len(series_a):
        raise SignalConditionError(
            "SIGNAL_CROSS_INDEX_INVALID", "index >=1 ve seri sınırları içinde olmalıdır."
        )
    prev_a, prev_b = series_a[index - 1], series_b[index - 1]
    curr_a, curr_b = series_a[index], series_b[index]
    if None in (prev_a, prev_b, curr_a, curr_b):
        return "UNKNOWN"
    was_above = prev_a > prev_b
    now_above = curr_a > curr_b
    if direction == "UP":
        return "TRUE" if (not was_above and now_above) else "FALSE"
    return "TRUE" if (was_above and not now_above) else "FALSE"


def evaluate(node: Node) -> TriState:
    """Pure, recursive Kleene (strong three-valued logic) evaluation."""

    if isinstance(node, Condition):
        return node.value
    if isinstance(node, CrossUp):
        return _cross(node.series_a, node.series_b, node.index, direction="UP")
    if isinstance(node, CrossDown):
        return _cross(node.series_a, node.series_b, node.index, direction="DOWN")
    if isinstance(node, Not):
        inner = evaluate(node.child)
        return "UNKNOWN" if inner == "UNKNOWN" else ("FALSE" if inner == "TRUE" else "TRUE")
    if isinstance(node, All):
        if not node.children:
            raise SignalConditionError("SIGNAL_AST_EMPTY_GROUP", "All en az bir çocuk gerektirir.")
        results = [evaluate(child) for child in node.children]
        if "FALSE" in results:
            return "FALSE"
        if "UNKNOWN" in results:
            return "UNKNOWN"
        return "TRUE"
    if isinstance(node, Any_):
        if not node.children:
            raise SignalConditionError("SIGNAL_AST_EMPTY_GROUP", "Any en az bir çocuk gerektirir.")
        results = [evaluate(child) for child in node.children]
        if "TRUE" in results:
            return "TRUE"
        if "UNKNOWN" in results:
            return "UNKNOWN"
        return "FALSE"
    raise SignalConditionError("SIGNAL_AST_NODE_INVALID", f"Bilinmeyen node tipi: {type(node)!r}")


def should_act(node: Node) -> bool:
    """Action fires only on a definite TRUE -- FALSE and UNKNOWN both
    withhold action (RG-09: "aksiyon yalnız kesin TRUE")."""

    return evaluate(node) == "TRUE"
