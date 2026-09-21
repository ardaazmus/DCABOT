"""Read-only dashboard aggregation over local stores (F28).

Counts and exact cash totals only. No valuation, no venue data, no
forecast — the numbers shown are the stores' own numbers.
"""
from dcabot.domain.numbers import exact_text, number


class DashboardError(ValueError):
    """Raised when dashboard inputs are not safely aggregatable."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def build_dashboard(
    *,
    paper: list[dict[str, object]],
    bots: list[dict[str, object]],
    deals: list[dict[str, object]],
    backups: list[dict[str, object]],
) -> dict[str, object]:
    """Aggregate local-store snapshots into one read-only dashboard."""
    for name, value in (
        ("paper", paper), ("bots", bots), ("deals", deals), ("backups", backups)
    ):
        if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
            raise DashboardError(
                "DASHBOARD_INPUT_INVALID", f"Dashboard girdisi liste olmalıdır: {name}."
            )
    cash_total = number("0")
    positions = 0
    open_orders = 0
    for session in paper:
        cash = session.get("cash")
        if not isinstance(cash, str):
            raise DashboardError("DASHBOARD_CASH_INVALID", "Paper nakdi string olmalıdır.")
        try:
            cash_total += number(cash)
        except ValueError as error:
            raise DashboardError(
                "DASHBOARD_CASH_INVALID", "Paper nakdi exact decimal olmalıdır."
            ) from error
        session_positions = session.get("positions", [])
        session_orders = session.get("orders", [])
        if not isinstance(session_positions, list) or not isinstance(session_orders, list):
            raise DashboardError("DASHBOARD_INPUT_INVALID", "Paper pozisyon/emir liste olmalıdır.")
        positions += len(session_positions)
        open_orders += sum(
            1 for order in session_orders
            if isinstance(order, dict) and order.get("status") == "OPEN"
        )
    bound_sessions = 0
    for bot in bots:
        sessions = bot.get("sessions", {})
        if not isinstance(sessions, dict):
            raise DashboardError("DASHBOARD_INPUT_INVALID", "Bot session eşlemi geçersiz.")
        bound_sessions += len(sessions)
    by_status: dict[str, int] = {}
    for deal in deals:
        status = deal.get("status")
        if not isinstance(status, str):
            raise DashboardError("DASHBOARD_INPUT_INVALID", "Deal durumu string olmalıdır.")
        by_status[status] = by_status.get(status, 0) + 1
    return {
        "paper": {
            "sessions": len(paper),
            "total_cash": exact_text(cash_total),
            "positions": positions,
            "open_orders": open_orders,
        },
        "bots": {"bots": len(bots), "bound_sessions": bound_sessions},
        "deals": {"deals": len(deals), "by_status": by_status},
        "backups": {"backups": len(backups)},
    }
