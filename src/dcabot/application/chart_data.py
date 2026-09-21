"""Bounded read-only chart data derived from verified canonical bars."""

from dataclasses import dataclass

from dcabot.application.historical_simulation import MAX_HISTORICAL_SIMULATION_BARS
from dcabot.data_adapters.historical import HistoricalDatasetInput


class HistoricalChartDataError(ValueError):
    """Raised when a dataset cannot satisfy the bounded chart-data contract."""


@dataclass(frozen=True, slots=True)
class HistoricalChartBar:
    """One canonical closed bar projected for a future read-only chart."""

    bar_index: int
    open_time_us: int
    close_time_us: int
    open: str
    high: str
    low: str
    close: str
    base_volume: str


def build_historical_chart_data(dataset: HistoricalDatasetInput) -> tuple[HistoricalChartBar, ...]:
    """Project verified bars without recalculating or changing financial values."""

    if len(dataset.bars) > MAX_HISTORICAL_SIMULATION_BARS:
        raise HistoricalChartDataError("Chart veri kapsamı server sınırını aşıyor.")
    return tuple(
        HistoricalChartBar(
            bar_index=index,
            open_time_us=bar.open_time_us,
            close_time_us=bar.close_time_us,
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            base_volume=bar.base_volume,
        )
        for index, bar in enumerate(dataset.bars, start=1)
    )
