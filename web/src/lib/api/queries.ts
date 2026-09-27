"use client";

import { useQuery } from "@tanstack/react-query";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { ApiHttpError, ApiNetworkError, apiDelete, apiGet, apiPost } from "./client";
import {
  backtestEnvelopeSchema,
  backupTakenSchema,
  backupVerifySchema,
  backupsSchema,
  bollingerSchema,
  botDealsEnvelopeSchema,
  botEnvelopeSchema,
  botEventsEnvelopeSchema,
  botReplayEnvelopeSchema,
  botStatsEnvelopeSchema,
  botsSchema,
  byBotEnvelopeSchema,
  byPairEnvelopeSchema,
  canarySchema,
  capabilitiesSchema,
  datasetsSchema,
  dealsEnvelopeSchema,
  dealDetailEnvelopeSchema,
  depthSchema,
  dealPlanEnvelopeSchema,
  dailyProfitEnvelopeSchema,
  downloadJobResponseSchema,
  downloadStartSchema,
  equityEnvelopeSchema,
  eventsSchema,
  anyGridStateEnvelopeSchema,
  futuresGridPreviewEnvelopeSchema,
  gridPreviewEnvelopeSchema,
  notificationStateSchema,
  telegramStatusEnvelopeSchema,
  telegramTestEnvelopeSchema,
  exchangeSymbolsSchema,
  healthSchema,
  killSwitchSchema,
  klinesSchema,
  macdSchema,
  portfolioSummaryEnvelopeSchema,
  regimeSchema,
  riskExplainSchema,
  seriesIndicatorSchema,
  stochRsiSchema,
  symbolRulesSchema,
  systemStatusSchema,
  testnetAccountSchema,
  testnetOrdersSchema,
  ticker24hSchema,
  tickers24hSchema,
  type BacktestEnvelope,
  type BackupTaken,
  type BackupVerify,
  type Backups,
  type Bollinger,
  type BotDealsEnvelope,
  type BotEnvelope,
  type BotEventsEnvelope,
  type BotReplayEnvelope,
  type BotStatsEnvelope,
  type Bots,
  type ByBotEnvelope,
  type ByPairEnvelope,
  type Canary,
  type Capabilities,
  type Datasets,
  type DcaStrategy,
  type DealDetailEnvelope,
  type DealPlanEnvelope,
  type DealsEnvelope,
  type Depth,
  type DailyProfitEnvelope,
  type DownloadJob,
  type DownloadStart,
  type EquityEnvelope,
  type Events,
  type AnyGridStateEnvelope,
  type FuturesGridBotStrategy,
  type FuturesGridPreviewEnvelope,
  type GridBotStrategy,
  type GridPreviewEnvelope,
  type TelegramStatusEnvelope,
  type TelegramTestEnvelope,
  type NotificationState,
  type ExchangeSymbols,
  type Health,
  type KillSwitch,
  type Klines,
  type Macd,
  type PortfolioSummaryEnvelope,
  type Regime,
  type RiskExplain,
  type SeriesIndicator,
  type StochRsi,
  type SymbolRules,
  type TestnetAccount,
  type TestnetOrders,
  type Ticker24h,
  type Tickers24h,
} from "./schemas";

export function useHealth(refetchInterval?: number | false) {
  return useQuery<Health>({
    queryKey: ["health"],
    queryFn: () => apiGet("/api/health", healthSchema),
    refetchInterval,
  });
}

export function useCapabilities() {
  return useQuery<Capabilities>({
    queryKey: ["capabilities"],
    queryFn: () => apiGet("/api/capabilities", capabilitiesSchema),
  });
}

export function useCanary() {
  return useQuery<Canary>({
    queryKey: ["canary"],
    queryFn: () => apiGet("/api/risk/canary", canarySchema),
  });
}

export function useEvents(limit = 20) {
  return useQuery<Events>({
    queryKey: ["events", limit],
    queryFn: () => apiGet(`/api/events?limit=${limit}`, eventsSchema),
  });
}

export function useNotificationState() {
  return useQuery<NotificationState>({
    queryKey: ["notifications-state"],
    queryFn: () => apiGet("/api/notifications/state", notificationStateSchema),
  });
}

export function useTelegramStatus() {
  return useQuery<TelegramStatusEnvelope>({
    queryKey: ["telegram-status"],
    queryFn: () => apiGet("/api/notifications/telegram", telegramStatusEnvelopeSchema),
  });
}

export type TelegramConfigureBody = { token: string; chat_id: string; enabled: boolean };

export function useTelegramConfigure() {
  const queryClient = useQueryClient();
  return useMutation<TelegramStatusEnvelope, Error, TelegramConfigureBody>({
    mutationFn: (body) => apiPost("/api/notifications/telegram/configure", body, telegramStatusEnvelopeSchema),
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ["telegram-status"] });
    },
  });
}

export function useTelegramTest() {
  return useMutation<TelegramTestEnvelope, Error, void>({
    mutationFn: () => apiPost("/api/notifications/telegram/test", {}, telegramTestEnvelopeSchema),
  });
}

export function useTelegramEnabled() {
  const queryClient = useQueryClient();
  return useMutation<TelegramStatusEnvelope, Error, { enabled: boolean }>({
    mutationFn: (body) => apiPost("/api/notifications/telegram/enabled", body, telegramStatusEnvelopeSchema),
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ["telegram-status"] });
    },
  });
}

export function useTelegramForget() {
  const queryClient = useQueryClient();
  return useMutation<TelegramStatusEnvelope, Error, void>({
    mutationFn: () => apiDelete("/api/notifications/telegram", telegramStatusEnvelopeSchema),
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ["telegram-status"] });
    },
  });
}

export type MarkReadBody = {
  upto_seq: number;
};

export function useMarkNotificationsRead() {
  const queryClient = useQueryClient();
  return useMutation<NotificationState, Error, MarkReadBody>({
    mutationFn: (body) => apiPost("/api/notifications/read", body, notificationStateSchema),
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ["notifications-state"] });
      void queryClient.invalidateQueries({ queryKey: ["events"] });
    },
  });
}

export function useExchangeSymbols(enabled = true) {
  return useQuery<ExchangeSymbols>({
    queryKey: ["exchange-symbols"],
    queryFn: () => apiGet("/api/public/exchange-symbols", exchangeSymbolsSchema),
    enabled,
    // Borsa sembol listesi gün içinde değişmez; bir kez al, sakla.
    staleTime: Infinity,
    gcTime: 1000 * 60 * 60,
  });
}

export function useBots(includeArchived = false) {
  return useQuery<Bots>({
    queryKey: ["v2-bots", includeArchived],
    queryFn: () =>
      apiGet(
        includeArchived ? "/api/v2/bots?include_archived=true" : "/api/v2/bots",
        botsSchema,
      ),
  });
}

export function useBot(botId: string, enabled = true) {
  return useQuery<BotEnvelope>({
    queryKey: ["v2-bot", botId],
    queryFn: () => apiGet(`/api/v2/bots/${encodeURIComponent(botId)}`, botEnvelopeSchema),
    enabled: enabled && botId !== "",
  });
}

/** Bot çalışırken (RUNNING/PAUSED) 15 sn'de bir tazelenir, yoksa tek çekim. */
function botLiveInterval(status: string | undefined): number | false {
  return status === "RUNNING" || status === "PAUSED" ? 15_000 : false;
}

export function useBotStats(botId: string, status?: string) {
  return useQuery<BotStatsEnvelope>({
    queryKey: ["v2-bot-stats", botId],
    queryFn: () => apiGet(`/api/v2/bots/${encodeURIComponent(botId)}/stats`, botStatsEnvelopeSchema),
    refetchInterval: botLiveInterval(status),
  });
}

export function useBotDeals(botId: string, status?: string) {
  return useQuery<BotDealsEnvelope>({
    queryKey: ["v2-bot-deals", botId],
    queryFn: () => apiGet(`/api/v2/bots/${encodeURIComponent(botId)}/deals`, botDealsEnvelopeSchema),
    refetchInterval: botLiveInterval(status),
  });
}

export function useBotEvents(botId: string, limit: number, status?: string, enabled = true) {
  return useQuery<BotEventsEnvelope>({
    queryKey: ["v2-bot-events", botId, limit],
    queryFn: () =>
      apiGet(
        `/api/v2/bots/${encodeURIComponent(botId)}/events?limit=${limit}`,
        botEventsEnvelopeSchema,
      ),
    enabled,
    refetchInterval: botLiveInterval(status),
  });
}

export type BotPreviewBody = { budget: string; strategy: DcaStrategy };

/**
 * Canlı plan. Form 400 ms gecikmeyle dengelenir (bileşen tarafında);
 * sorgu anahtarı gövdenin kendisidir, yalnız en son gövdenin yanıtı
 * gösterilir.
 */
/**
 * Önizleme yeniden deneme kuralı: 422 form hatasıdır, son sözdür;
 * yalnız ağ kesintisi ve 5xx (yukarı-akım anlık hataları) iki kez
 * denenir.
 */
export function shouldRetryPreview(failureCount: number, error: Error): boolean {
  if (failureCount >= 2) return false;
  if (error instanceof ApiNetworkError) return true;
  return error instanceof ApiHttpError && error.status >= 500;
}

export function useBotPreview(body: BotPreviewBody | null) {
  return useQuery<DealPlanEnvelope>({
    queryKey: ["v2-preview", body],
    queryFn: () => apiPost("/api/v2/bots/preview", body, dealPlanEnvelopeSchema),
    enabled: body !== null,
    retry: shouldRetryPreview,
    staleTime: 30_000,
  });
}

export type BotCreateBody = {
  name: string;
  mode: string;
  budget: string;
  strategy: DcaStrategy;
};

export function useBotCreate() {
  const queryClient = useQueryClient();
  return useMutation<BotEnvelope, Error, BotCreateBody>({
    mutationFn: (body) => apiPost("/api/v2/bots", body, botEnvelopeSchema),
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ["v2-bots"] });
      void queryClient.invalidateQueries({ queryKey: ["v2-portfolio"] });
    },
  });
}

export type GridPreviewBody = { budget: string; strategy: GridBotStrategy };

export function useGridPreview(body: GridPreviewBody | null) {
  return useQuery<GridPreviewEnvelope>({
    queryKey: ["v2-grid-preview", body],
    queryFn: () => apiPost("/api/v2/grid-bots/preview", body, gridPreviewEnvelopeSchema),
    enabled: body !== null,
    retry: shouldRetryPreview,
    staleTime: 30_000,
  });
}

export type GridBotCreateBody = {
  name: string;
  mode: string;
  budget: string;
  strategy: GridBotStrategy;
};

export function useGridBotCreate() {
  const queryClient = useQueryClient();
  return useMutation<BotEnvelope, Error, GridBotCreateBody>({
    mutationFn: (body) => apiPost("/api/v2/grid-bots", body, botEnvelopeSchema),
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ["v2-bots"] });
      void queryClient.invalidateQueries({ queryKey: ["v2-portfolio"] });
    },
  });
}

export function useGridState(botId: string, status?: string, enabled = true) {
  return useQuery<AnyGridStateEnvelope>({
    queryKey: ["v2-grid-state", botId],
    queryFn: () => apiGet(`/api/v2/bots/${encodeURIComponent(botId)}/grid`, anyGridStateEnvelopeSchema),
    enabled,
    refetchInterval: botLiveInterval(status),
  });
}

export type FuturesGridPreviewBody = { budget: string; strategy: FuturesGridBotStrategy };

export function useFuturesGridPreview(body: FuturesGridPreviewBody | null) {
  return useQuery<FuturesGridPreviewEnvelope>({
    queryKey: ["v2-futures-grid-preview", body],
    queryFn: () => apiPost("/api/v2/futures-grid-bots/preview", body, futuresGridPreviewEnvelopeSchema),
    enabled: body !== null,
    retry: shouldRetryPreview,
    staleTime: 30_000,
  });
}

export type FuturesGridBotCreateBody = {
  name: string;
  mode: string;
  budget: string;
  strategy: FuturesGridBotStrategy;
};

export function useFuturesGridBotCreate() {
  const queryClient = useQueryClient();
  return useMutation<BotEnvelope, Error, FuturesGridBotCreateBody>({
    mutationFn: (body) => apiPost("/api/v2/futures-grid-bots", body, botEnvelopeSchema),
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ["v2-bots"] });
      void queryClient.invalidateQueries({ queryKey: ["v2-portfolio"] });
    },
  });
}

export type BacktestBody = {
  budget: string;
  strategy: DcaStrategy;
  interval: string;
  start_date: string;
  end_date: string;
};

/** Backtest koşusu; uzun istek `signal` ile iptal edilir. Yeniden deneme yok. */
export function useBacktestRun() {
  return useMutation<BacktestEnvelope, Error, { body: BacktestBody; signal?: AbortSignal }>({
    mutationFn: ({ body, signal }) =>
      apiPost("/api/v2/backtests", body, backtestEnvelopeSchema, { signal }),
    retry: false,
  });
}

export function useDeals(status: "active" | "closed", limit = 100) {
  return useQuery<DealsEnvelope>({
    queryKey: ["v2-deals", status, limit],
    queryFn: () =>
      apiGet(`/api/v2/deals?status=${status}&limit=${limit}`, dealsEnvelopeSchema),
    // Aktif deal'ler canlıdır; geçmiş sabittir.
    refetchInterval: status === "active" ? 15_000 : false,
  });
}

export type EquityRange = "7d" | "30d" | "all";

/** Kontrol merkezi KPI'ları; 30 sn'de bir tazelenir. */
export function usePortfolioSummary() {
  return useQuery<PortfolioSummaryEnvelope>({
    queryKey: ["v2-portfolio", "summary"],
    queryFn: () => apiGet("/api/v2/stats/portfolio/summary", portfolioSummaryEnvelopeSchema),
    refetchInterval: 30_000,
  });
}

/** Saatlik özsermaye serisi; anlık görüntüler saatte bir yazılır. */
export function usePortfolioEquity(range: EquityRange) {
  return useQuery<EquityEnvelope>({
    queryKey: ["v2-portfolio", "equity", range],
    queryFn: () =>
      apiGet(`/api/v2/stats/portfolio/equity?range=${range}`, equityEnvelopeSchema),
  });
}

/** Günlük gerçekleşmiş kâr (UTC günleri, sıfır dolgulu). */
export function useDailyProfit(days = 30) {
  return useQuery<DailyProfitEnvelope>({
    queryKey: ["v2-portfolio", "daily", days],
    queryFn: () =>
      apiGet(`/api/v2/stats/portfolio/daily-profit?days=${days}`, dailyProfitEnvelopeSchema),
  });
}

export function useProfitByBot() {
  return useQuery<ByBotEnvelope>({
    queryKey: ["v2-portfolio", "by-bot"],
    queryFn: () => apiGet("/api/v2/stats/portfolio/by-bot", byBotEnvelopeSchema),
    refetchInterval: 60_000,
  });
}

export function useProfitByPair() {
  return useQuery<ByPairEnvelope>({
    queryKey: ["v2-portfolio", "by-pair"],
    queryFn: () => apiGet("/api/v2/stats/portfolio/by-pair", byPairEnvelopeSchema),
    refetchInterval: 60_000,
  });
}

export function useDealDetail(botId: string, seq: number, enabled = true) {
  return useQuery<DealDetailEnvelope>({
    queryKey: ["v2-deal", botId, seq],
    queryFn: () =>
      apiGet(
        `/api/v2/bots/${encodeURIComponent(botId)}/deals/${seq}`,
        dealDetailEnvelopeSchema,
      ),
    enabled: enabled && botId !== "" && seq >= 1,
    // Yanıt gelene kadar ve açık deal'de 15 sn; kapanınca durur.
    refetchInterval: (query) => {
      const closed = query.state.data?.data.closed_at_us;
      return closed === null || closed === undefined ? 15_000 : false;
    },
  });
}

export type DealAction = "close" | "cancel" | "add-funds";

export function useDealAction() {
  const queryClient = useQueryClient();
  return useMutation<
    DealDetailEnvelope,
    Error,
    { botId: string; seq: number; action: DealAction; revision: number; amount?: string }
  >({
    mutationFn: ({ botId, seq, action, revision, amount }) =>
      apiPost(
        `/api/v2/bots/${encodeURIComponent(botId)}/deals/${seq}/${action}`,
        amount === undefined ? { revision } : { revision, amount },
        dealDetailEnvelopeSchema,
      ),
    onSettled: (_data, _error, variables) => {
      void queryClient.invalidateQueries({ queryKey: ["v2-deals"] });
      void queryClient.invalidateQueries({ queryKey: ["v2-deal", variables.botId, variables.seq] });
      void queryClient.invalidateQueries({ queryKey: ["v2-bot", variables.botId] });
      void queryClient.invalidateQueries({ queryKey: ["v2-bot-stats", variables.botId] });
      void queryClient.invalidateQueries({ queryKey: ["v2-bot-deals", variables.botId] });
      void queryClient.invalidateQueries({ queryKey: ["v2-bot-events", variables.botId] });
      void queryClient.invalidateQueries({ queryKey: ["v2-portfolio"] });
    },
  });
}

export type BotAction = "start" | "pause" | "resume" | "stop" | "archive";

export function useBotAction() {
  const queryClient = useQueryClient();
  return useMutation<BotEnvelope, Error, { botId: string; action: BotAction; revision: number }>({
    mutationFn: ({ botId, action, revision }) =>
      apiPost(
        `/api/v2/bots/${encodeURIComponent(botId)}/${action}`,
        { revision },
        botEnvelopeSchema,
      ),
    onSettled: (_data, _error, variables) => {
      void queryClient.invalidateQueries({ queryKey: ["v2-bots"] });
      void queryClient.invalidateQueries({ queryKey: ["v2-bot", variables.botId] });
      void queryClient.invalidateQueries({ queryKey: ["v2-bot-stats", variables.botId] });
      void queryClient.invalidateQueries({ queryKey: ["v2-bot-deals", variables.botId] });
      void queryClient.invalidateQueries({ queryKey: ["v2-bot-events", variables.botId] });
      void queryClient.invalidateQueries({ queryKey: ["v2-portfolio"] });
    },
  });
}

/** Bot kurulumunu taze bir bot olarak çoğaltır; listeyi tazeler. */
export function useBotCopy() {
  const queryClient = useQueryClient();
  return useMutation<BotEnvelope, Error, { botId: string; name?: string }>({
    mutationFn: ({ botId, name }) =>
      apiPost(
        `/api/v2/bots/${encodeURIComponent(botId)}/copy`,
        name === undefined ? {} : { name },
        botEnvelopeSchema,
      ),
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ["v2-bots"] });
    },
  });
}

export type BotReplayBody = {
  start_date: string;
  end_date: string;
};

/** Geçmiş çalıştırma; uzun istek, yeniden deneme yok. */
export function useBotReplay(botId: string) {
  const queryClient = useQueryClient();
  return useMutation<BotReplayEnvelope, Error, BotReplayBody>({
    mutationFn: (body) =>
      apiPost(
        `/api/v2/bots/${encodeURIComponent(botId)}/replay`,
        body,
        botReplayEnvelopeSchema,
      ),
    retry: false,
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ["v2-bot", botId] });
      void queryClient.invalidateQueries({ queryKey: ["v2-bot-stats", botId] });
      void queryClient.invalidateQueries({ queryKey: ["v2-bot-deals", botId] });
      void queryClient.invalidateQueries({ queryKey: ["v2-bot-events", botId] });
      void queryClient.invalidateQueries({ queryKey: ["v2-grid-state", botId] });
      void queryClient.invalidateQueries({ queryKey: ["v2-portfolio"] });
    },
  });
}

/**
 * Toplu 24s verisi. `symbols` sırası korunarak döner; en fazla 50 sembol.
 * Boş listede istek atılmaz.
 */
export function useTickers24h(symbols: readonly string[], refetchInterval?: number) {
  const key = symbols.join(",");
  return useQuery<Tickers24h>({
    queryKey: ["tickers-24h", key],
    queryFn: () =>
      apiGet(`/api/public/tickers-24h?symbols=${encodeURIComponent(key)}`, tickers24hSchema),
    enabled: symbols.length > 0,
    refetchInterval,
  });
}

export function useTicker24h(symbol: string) {
  return useQuery<Ticker24h>({
    queryKey: ["ticker-24h", symbol],
    queryFn: () =>
      apiGet(`/api/public/ticker-24h?symbol=${encodeURIComponent(symbol)}`, ticker24hSchema),
  });
}

export function useKlines(
  symbol: string,
  interval: string,
  limit: number,
  refetchInterval?: number,
) {
  return useQuery<Klines>({
    queryKey: ["klines", symbol, interval, limit],
    queryFn: () =>
      apiGet(
        `/api/public/klines?symbol=${encodeURIComponent(symbol)}&interval=${encodeURIComponent(interval)}&limit=${limit}`,
        klinesSchema,
      ),
    refetchInterval,
  });
}

export function useDepth(symbol: string, limit: number, options?: { paused?: boolean; refetchInterval?: number }) {
  return useQuery<Depth>({
    queryKey: ["depth", symbol, limit],
    queryFn: () =>
      apiGet(
        `/api/public/depth?symbol=${encodeURIComponent(symbol)}&limit=${limit}`,
        depthSchema,
      ),
    refetchInterval: options?.paused ? false : (options?.refetchInterval ?? 5000),
  });
}

export function useSma(closes: readonly string[], window: number, enabled: boolean) {
  return useQuery<SeriesIndicator>({
    queryKey: ["indicator-sma", window, closes.length, closes[0], closes[closes.length - 1]],
    queryFn: () => apiPost("/api/indicators/sma", { closes, window }, seriesIndicatorSchema),
    enabled: enabled && closes.length >= 2,
    staleTime: 30_000,
  });
}

export function useEma(closes: readonly string[], window: number, enabled: boolean) {
  return useQuery<SeriesIndicator>({
    queryKey: ["indicator-ema", window, closes.length, closes[0], closes[closes.length - 1]],
    queryFn: () => apiPost("/api/indicators/ema", { closes, window }, seriesIndicatorSchema),
    enabled: enabled && closes.length >= 2,
    staleTime: 30_000,
  });
}

export function useBollinger(
  closes: readonly string[],
  window: number,
  numStd: string,
  enabled: boolean,
) {
  return useQuery<Bollinger>({
    queryKey: ["indicator-bollinger", window, numStd, closes.length, closes[0], closes[closes.length - 1]],
    queryFn: () =>
      apiPost("/api/indicators/bollinger", { closes, window, num_std: numStd }, bollingerSchema),
    enabled: enabled && closes.length >= 2,
    staleTime: 30_000,
  });
}

export function useMacd(
  closes: readonly string[],
  params: { fast: number; slow: number; signal: number; scale: number },
  enabled: boolean,
) {
  const { fast, slow, signal, scale } = params;
  return useQuery<Macd>({
    queryKey: ["indicator-macd", fast, slow, signal, scale, closes.length, closes[0], closes[closes.length - 1]],
    queryFn: () => apiPost("/api/indicators/macd", { closes, fast, slow, signal, scale }, macdSchema),
    enabled: enabled && closes.length >= 2,
    staleTime: 30_000,
  });
}

export function useStochRsi(
  closes: readonly string[],
  params: { rsi_window: number; stoch_window: number; scale: number },
  enabled: boolean,
) {
  const { rsi_window, stoch_window, scale } = params;
  return useQuery<StochRsi>({
    queryKey: ["indicator-stoch-rsi", rsi_window, stoch_window, scale, closes.length, closes[0], closes[closes.length - 1]],
    queryFn: () =>
      apiPost("/api/indicators/stoch-rsi", { closes, rsi_window, stoch_window, scale }, stochRsiSchema),
    enabled: enabled && closes.length >= 2,
    staleTime: 30_000,
  });
}

export function useSymbolRules(symbol: string, enabled = true) {
  return useQuery<SymbolRules>({
    queryKey: ["symbol-rules", symbol],
    queryFn: () =>
      apiGet(
        `/api/public/symbol-rules?symbol=${encodeURIComponent(symbol)}`,
        symbolRulesSchema,
      ),
    enabled: enabled && symbol !== "",
    staleTime: 60_000,
  });
}

export function useTestnetAccount() {
  return useQuery<TestnetAccount>({
    queryKey: ["testnet-account"],
    queryFn: () => apiGet("/api/testnet/account", testnetAccountSchema),
    retry: false,
  });
}

export function useTestnetOrders(enabled: boolean) {
  return useQuery<TestnetOrders>({
    queryKey: ["testnet-orders"],
    queryFn: () => apiGet("/api/testnet/open-orders", testnetOrdersSchema),
    enabled,
    retry: false,
  });
}

export function useKillSwitch() {
  const queryClient = useQueryClient();
  return useMutation<KillSwitch, Error, { engaged: boolean; reason?: string }>({
    mutationFn: (body) => apiPost("/api/risk/kill-switch", body, killSwitchSchema),
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ["canary"] });
    },
  });
}

export function useRiskExplain() {
  return useMutation<
    RiskExplain,
    Error,
    { bot_id?: string; symbol?: string; session_id?: string; deal_id?: string }
  >({
    mutationFn: (body) => apiPost("/api/risk/explain", body, riskExplainSchema),
  });
}

export function useDatasets() {
  return useQuery<Datasets>({
    queryKey: ["datasets"],
    queryFn: () => apiGet("/api/datasets", datasetsSchema),
  });
}

export function useDownloadStart() {
  return useMutation<DownloadStart, Error, { dataset_id: string }>({
    mutationFn: (body) => apiPost("/api/dataset-downloads", body, downloadStartSchema),
  });
}

export function useDownloadJob(jobId: string | null, refetchInterval?: number | false) {
  return useQuery<DownloadJob>({
    queryKey: ["download-job", jobId],
    queryFn: () => apiGet(`/api/dataset-downloads/${jobId}`, downloadJobResponseSchema),
    enabled: jobId !== null,
    refetchInterval: refetchInterval ?? 2000,
  });
}

export function useDownloadCancel() {
  return useMutation<DownloadJob, Error, string>({
    mutationFn: (jobId) =>
      apiPost(`/api/dataset-downloads/${jobId}/cancel`, {}, downloadJobResponseSchema),
  });
}

export function useBackups() {
  return useQuery<Backups>({
    queryKey: ["backups"],
    queryFn: () => apiGet("/api/admin/backups", backupsSchema),
  });
}

export function useBackupTake() {
  const queryClient = useQueryClient();
  return useMutation<BackupTaken, Error, { store: string }>({
    mutationFn: (body) => apiPost("/api/admin/backup", body, backupTakenSchema),
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ["backups"] });
    },
  });
}

export function useBackupVerify() {
  return useMutation<BackupVerify, Error, { backup_file: string }>({
    mutationFn: (body) => apiPost("/api/admin/backup/verify", body, backupVerifySchema),
  });
}

export function useSystemStatus() {
  return useQuery({
    queryKey: ["system-status"],
    queryFn: () => apiGet("/api/system/status", systemStatusSchema),
  });
}

export type RegimeBar = { high: string; low: string; close: string };

export function useRegime(
  bars: readonly RegimeBar[],
  params: {
    adx_window: number;
    bb_window: number;
    bb_num_std: string;
    trend_threshold: string;
    range_threshold: string;
    squeeze_threshold: string;
    min_di_separation: string;
  },
  enabled: boolean,
) {
  return useQuery<Regime>({
    // Rejim yalnız son noktayı değerlendirir; kimlikte son mum yeter.
    queryKey: ["regime", bars.length, bars[bars.length - 1]],
    queryFn: () => apiPost("/api/risk/regime", { bars, ...params }, regimeSchema),
    enabled: enabled && bars.length >= 2,
    staleTime: 60_000,
  });
}
