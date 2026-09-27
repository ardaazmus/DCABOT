"use client";

import { useTranslations } from "next-intl";
import { use, useMemo, useState } from "react";

import { ChartCard } from "@/components/chart-card";
import { EmptyState } from "@/components/empty-state";
import { BotSetupButton } from "@/components/market/bot-setup-button";
import { FavoriteStar } from "@/components/market/favorite-star";
import { IndicatorPanel } from "@/components/market/indicator-panel";
import { OrderBook } from "@/components/market/order-book";
import { PriceChart, type ChartOverlay } from "@/components/market/price-chart";
import { RegimeCard } from "@/components/market/regime-card";
import { Price } from "@/components/money";
import { Pnl } from "@/components/pnl";
import { Skeleton } from "@/components/skeleton";
import { VolumeCompact } from "@/components/volume-compact";
import {
  useBollinger,
  useDepth,
  useEma,
  useExchangeSymbols,
  useKlines,
  useMacd,
  useRegime,
  useSma,
  useStochRsi,
  useTicker24h,
  type RegimeBar,
} from "@/lib/api/queries";
import { pointsToHistogram, pointsToSegments } from "@/lib/chart/indicators";
import { barsToCandles, microsToTimestamp } from "@/lib/chart/klines";
import { paletteSnapshot } from "@/lib/chart/theme";
import { isDecimalString, type DecimalString } from "@/lib/decimal";
import { cn } from "@/lib/utils";

type Interval = "15m" | "1h" | "4h" | "1d";
const INTERVALS: Interval[] = ["15m", "1h", "4h", "1d"];
const KLINES_LIMIT = 300;
const REGIME_BARS = 300;

const REGIME_PARAMS = {
  adx_window: 14,
  bb_window: 20,
  bb_num_std: "2",
  trend_threshold: "25",
  range_threshold: "20",
  squeeze_threshold: "0.05",
  min_di_separation: "0",
} as const;

const MACD_PARAMS = { fast: 12, slow: 26, signal: 9, scale: 8 } as const;
const STOCH_PARAMS = { rsi_window: 14, stoch_window: 14, scale: 8 } as const;

function toDecimal(text: string | undefined): DecimalString | undefined {
  return text !== undefined && isDecimalString(text) ? text : undefined;
}

export default function MarketSymbolPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol: rawSymbol } = use(params);
  const symbol = rawSymbol.toUpperCase();
  const t = useTranslations("symbol");
  const tm = useTranslations("market");

  const [interval, setInterval] = useState<Interval>("1h");
  const [showSma, setShowSma] = useState(false);
  const [showEma, setShowEma] = useState(false);
  const [showBb, setShowBb] = useState(false);
  const [showMacd, setShowMacd] = useState(false);
  const [showStoch, setShowStoch] = useState(false);
  const [depthPaused, setDepthPaused] = useState(false);

  const ticker = useTicker24h(symbol);
  const klines = useKlines(symbol, interval, KLINES_LIMIT, 30_000);
  const klines1h = useKlines(symbol, "1h", KLINES_LIMIT);
  const depth = useDepth(symbol, 20, { paused: depthPaused, refetchInterval: 5000 });
  const symbols = useExchangeSymbols(true);

  const bars = useMemo(() => klines.data?.data.bars ?? [], [klines.data]);
  const closes: readonly string[] = useMemo(() => bars.map((bar) => bar.close), [bars]);
  const candles = useMemo(() => barsToCandles(bars), [bars]);
  const times = useMemo(() => bars.map((bar) => microsToTimestamp(bar.open_time_us)), [bars]);

  const sma = useSma(closes, 20, showSma);
  const ema = useEma(closes, 50, showEma);
  const bollinger = useBollinger(closes, 20, "2", showBb);
  const macd = useMacd(closes, MACD_PARAMS, showMacd);
  const stoch = useStochRsi(closes, STOCH_PARAMS, showStoch);

  const regimeBars: readonly RegimeBar[] = useMemo(() => {
    const all = klines1h.data?.data.bars ?? [];
    return all
      .slice(-REGIME_BARS)
      .map((bar) => ({ high: bar.high, low: bar.low, close: bar.close }));
  }, [klines1h.data]);
  const regime = useRegime(regimeBars, REGIME_PARAMS, regimeBars.length >= 2);

  const overlays: ChartOverlay[] = useMemo(() => {
    const list: ChartOverlay[] = [];
    if (showSma && sma.data !== undefined) {
      list.push({
        id: "sma",
        color: "entry",
        segments: pointsToSegments(sma.data.data.points, (p) => p.value, times),
      });
    }
    if (showEma && ema.data !== undefined) {
      list.push({
        id: "ema",
        color: "safety",
        segments: pointsToSegments(ema.data.data.points, (p) => p.value, times),
      });
    }
    if (showBb && bollinger.data !== undefined) {
      const points = bollinger.data.data.points;
      list.push(
        { id: "bb-upper", color: "accent", dashed: true, segments: pointsToSegments(points, (p) => p.upper, times) },
        { id: "bb-middle", color: "accent", segments: pointsToSegments(points, (p) => p.middle, times) },
        { id: "bb-lower", color: "accent", dashed: true, segments: pointsToSegments(points, (p) => p.lower, times) },
      );
    }
    return list;
  }, [showSma, showEma, showBb, sma.data, ema.data, bollinger.data, times]);

  const palette = useMemo(() => paletteSnapshot(), []);
  const macdHistogram = useMemo(
    () =>
      macd.data === undefined
        ? undefined
        : pointsToHistogram(macd.data.data.points, (p) => p.histogram, times, {
            up: palette.profit,
            down: palette.loss,
            neutral: palette.muted,
          }),
    [macd.data, times, palette],
  );
  const macdLines = useMemo(() => {
    if (macd.data === undefined) return [];
    const points = macd.data.data.points;
    return [
      { id: "macd", color: "accent" as const, segments: pointsToSegments(points, (p) => p.macd, times) },
      { id: "signal", color: "safety" as const, segments: pointsToSegments(points, (p) => p.signal, times) },
    ];
  }, [macd.data, times]);
  const stochLines = useMemo(() => {
    if (stoch.data === undefined) return [];
    const points = stoch.data.data.points;
    return [
      { id: "rsi", color: "entry" as const, segments: pointsToSegments(points, (p) => p.rsi, times) },
      { id: "stoch", color: "safety" as const, segments: pointsToSegments(points, (p) => p.stoch_rsi, times) },
    ];
  }, [stoch.data, times]);

  const quoteAsset = symbols.data?.symbols.find((entry) => entry.symbol === symbol)?.quote_asset;
  const dataKey = `${interval}-${closes.length}-${closes[closes.length - 1] ?? ""}`;

  const settled = !ticker.isPending && !klines.isPending;
  if (settled && (ticker.isError || klines.isError)) {
    return (
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-2">
        <h1 className="font-mono text-2xl font-semibold tracking-tight">{symbol}</h1>
        <EmptyState
          title={t("notFound")}
          description={t("notFoundHint")}
          actionLabel={t("backToMarket")}
          actionHref="/market"
        />
      </div>
    );
  }

  const chips = [
    { id: "sma", label: t("sma"), on: showSma, toggle: () => setShowSma((v) => !v) },
    { id: "ema", label: t("ema"), on: showEma, toggle: () => setShowEma((v) => !v) },
    { id: "bb", label: t("bollinger"), on: showBb, toggle: () => setShowBb((v) => !v) },
    { id: "macd", label: t("macd"), on: showMacd, toggle: () => setShowMacd((v) => !v) },
    { id: "stoch", label: t("stochRsi"), on: showStoch, toggle: () => setShowStoch((v) => !v) },
  ];
  const indicatorPending =
    (showSma && sma.isPending) ||
    (showEma && ema.isPending) ||
    (showBb && bollinger.isPending) ||
    (showMacd && macd.isPending) ||
    (showStoch && stoch.isPending);

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-4">
      {/* Başlık */}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="flex items-center gap-2">
          <h1 className="font-mono text-2xl font-semibold tracking-tight">{symbol}</h1>
          <FavoriteStar symbol={symbol} />
        </div>
        <BotSetupButton symbol={symbol} />
      </div>
      {ticker.isPending ? (
        <div className="flex gap-6">
          <Skeleton className="h-9 w-40" />
          <Skeleton className="h-9 w-24" />
          <Skeleton className="h-9 w-32" />
        </div>
      ) : ticker.data === undefined ? null : (
        <div data-testid="symbol-stats" className="flex flex-wrap items-baseline gap-x-6 gap-y-1">
          <span className="text-3xl font-semibold">
            <Price value={toDecimal(ticker.data.last_price)} />
          </span>
          <Pnl value={toDecimal(ticker.data.price_change_percent)} variant="percent" />
          <span className="text-sm text-muted-foreground">
            {tm("volume")}:{" "}
            <VolumeCompact value={toDecimal(ticker.data.quote_volume)} suffix={quoteAsset} />
          </span>
        </div>
      )}

      {/* Mum grafiği */}
      <ChartCard
        title={t("chart")}
        ranges={INTERVALS.map((id) => ({ id, label: id }))}
        activeRange={interval}
        onRangeChange={(id) => setInterval(id as Interval)}
        state={klines.isPending ? "loading" : klines.isError ? "error" : "ready"}
        error={t("notFoundHint")}
      >
        <div className="flex flex-col gap-2">
          {klines.data !== undefined && !klines.data.data.last_bar_closed ? (
            <p className="flex items-center gap-2 text-xs text-muted-foreground">
              <span className="size-1.5 animate-pulse rounded-full bg-safety" aria-hidden="true" />
              {t("forming")}
            </p>
          ) : null}
          <PriceChart candles={candles} overlays={overlays} label={t("chart")} />
        </div>
      </ChartCard>

      {/* İndikatör çipleri */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-medium">{t("indicators")}:</span>
        {chips.map((chip) => (
          <button
            key={chip.id}
            type="button"
            aria-pressed={chip.on}
            onClick={chip.toggle}
            className={cn(
              "rounded-md px-3 py-1.5 font-mono text-sm font-medium",
              chip.on ? "bg-accent/12 text-accent" : "text-muted-foreground hover:bg-muted",
            )}
          >
            {chip.label}
          </button>
        ))}
        {indicatorPending ? (
          <span role="status" className="text-xs text-muted-foreground">
            …
          </span>
        ) : null}
      </div>

      {/* Alt paneller */}
      {showMacd ? (
        <ChartCard
          title={t("macd")}
          state={macd.isPending ? "loading" : macd.isError ? "error" : "ready"}
          error={t("notFoundHint")}
        >
          <IndicatorPanel
            lines={macdLines}
            histogram={macdHistogram}
            label={t("macd")}
            testId="macd-panel"
            dataKey={dataKey}
          />
        </ChartCard>
      ) : null}
      {showStoch ? (
        <ChartCard
          title={t("stochRsi")}
          state={stoch.isPending ? "loading" : stoch.isError ? "error" : "ready"}
          error={t("notFoundHint")}
        >
          <IndicatorPanel
            lines={stochLines}
            label={t("stochRsi")}
            testId="stoch-panel"
            dataKey={dataKey}
          />
        </ChartCard>
      ) : null}

      {/* Defter + rejim */}
      <div className="grid gap-4 lg:grid-cols-2">
        {depth.isPending && depth.data === undefined ? (
          <Skeleton className="h-96 w-full" />
        ) : depth.data === undefined ? (
          <p role="alert" className="text-sm text-loss">
            {t("notFoundHint")}
          </p>
        ) : (
          <OrderBook
            depth={depth.data}
            paused={depthPaused}
            onTogglePause={() => setDepthPaused((v) => !v)}
          />
        )}
        {regime.isPending ? (
          <Skeleton className="h-48 w-full" />
        ) : regime.isError || regime.data === undefined ? (
          <p role="alert" className="text-sm text-loss">
            {t("regimeError")}
          </p>
        ) : (
          <div data-testid="regime-card">
            <RegimeCard regime={regime.data} />
          </div>
        )}
      </div>
    </div>
  );
}
