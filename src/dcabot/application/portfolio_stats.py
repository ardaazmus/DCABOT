"""Exact portfolio statistics over paper bots (Faz W-B5).

Everything is Fraction arithmetic over values the runner stored; the
equity series comes from the periodic snapshot table the runner writes.
Archived bots are excluded everywhere. "Today" and day buckets use UTC
midnights; only CLOSED deals count as realized profit.
"""

from fractions import Fraction

from dcabot.application.bot_stats import bot_statistics
from dcabot.domain.numbers import exact_text, number
from dcabot.persistence.bot_store import BotDeal, BotRecord, BotRuntime

DAY_US = 86_400_000_000
SNAPSHOT_INTERVAL_US = 3_600_000_000
SNAPSHOT_RETENTION_US = 90 * DAY_US
ACTIVE_STATUSES = ("RUNNING", "PAUSED")


def _live(records: tuple[BotRecord, ...]) -> tuple[BotRecord, ...]:
    return tuple(record for record in records if record.archived_at_us is None)


def portfolio_equity(
    records: tuple[BotRecord, ...],
    deals_by_bot: dict[str, tuple[BotDeal, ...]],
    runtimes: dict[str, BotRuntime],
) -> dict[str, str]:
    """Live equity: budget + realized + open-deal unrealized per bot."""

    equity = realized = unrealized = Fraction(0)
    for record in _live(records):
        stats = bot_statistics(
            tuple(deals_by_bot.get(record.bot_id, ())), runtimes.get(record.bot_id), budget=record.budget
        )
        bot_realized = number(stats["total_profit"])
        active = stats["active_deal"]
        bot_unrealized = number(active["unrealized_profit"]) if active is not None and active["unrealized_profit"] is not None else Fraction(0)
        equity += number(record.budget) + bot_realized + bot_unrealized
        realized += bot_realized
        unrealized += bot_unrealized
    return {"equity": exact_text(equity), "realized": exact_text(realized), "unrealized": exact_text(unrealized)}


def portfolio_summary(
    records: tuple[BotRecord, ...],
    deals_by_bot: dict[str, tuple[BotDeal, ...]],
    runtimes: dict[str, BotRuntime],
    now_us: int,
) -> dict[str, object]:
    """Control-center KPIs: total value, today's realized profit, active
    bots (RUNNING/PAUSED) and the capital deployed in them."""

    live = _live(records)
    equity = portfolio_equity(live, deals_by_bot, runtimes)
    today = now_us // DAY_US
    today_profit = sum(
        (
            number(deal.profit)
            for record in live
            for deal in deals_by_bot.get(record.bot_id, ())
            if deal.closed_at_us is not None and deal.closed_at_us // DAY_US == today
        ),
        Fraction(0),
    )
    active = [record for record in live if record.status in ACTIVE_STATUSES]
    deployed = sum((number(record.budget) for record in active), Fraction(0))
    return {
        "total_value": equity["equity"],
        "today_profit": exact_text(today_profit),
        "active_bots": len(active),
        "deployed_capital": exact_text(deployed),
    }


def daily_profit(deals: tuple[BotDeal, ...], days: int, now_us: int) -> list[dict[str, object]]:
    """Realized profit per UTC day, oldest first, zero-filled."""

    if type(days) is not int or not 1 <= days <= 90:
        raise ValueError("days must be within 1..90")
    first_day = now_us // DAY_US - days + 1
    buckets = [Fraction(0)] * days
    for deal in deals:
        if deal.closed_at_us is None or deal.profit is None:
            continue
        index = deal.closed_at_us // DAY_US - first_day
        if 0 <= index < days:
            buckets[index] += number(deal.profit)
    return [{"day_start_us": (first_day + index) * DAY_US, "profit": exact_text(total)} for index, total in enumerate(buckets)]


def profit_by_bot(
    records: tuple[BotRecord, ...], deals_by_bot: dict[str, tuple[BotDeal, ...]]
) -> list[dict[str, object]]:
    """Realized profit per bot, in store (creation) order."""

    rows = []
    for record in _live(records):
        closed = [deal for deal in deals_by_bot.get(record.bot_id, ()) if deal.closed_at_us is not None]
        total = sum((number(deal.profit) for deal in closed), Fraction(0))
        rows.append(
            {"bot_id": record.bot_id, "bot_name": record.name, "profit": exact_text(total), "deals_completed": len(closed)}
        )
    return rows


def profit_by_pair(
    records: tuple[BotRecord, ...], deals_by_bot: dict[str, tuple[BotDeal, ...]]
) -> list[dict[str, object]]:
    """Realized profit per symbol, symbols ascending."""

    totals: dict[str, list] = {}
    for record in _live(records):
        closed = [deal for deal in deals_by_bot.get(record.bot_id, ()) if deal.closed_at_us is not None]
        entry = totals.setdefault(record.symbol, [Fraction(0), 0, 0])
        entry[0] += sum((number(deal.profit) for deal in closed), Fraction(0))
        entry[1] += len(closed)
        entry[2] += 1
    return [
        {"symbol": symbol, "profit": exact_text(total), "deals_completed": count, "bots": bots}
        for symbol, (total, count, bots) in sorted(totals.items())
    ]
