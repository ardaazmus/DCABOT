import { z } from "zod";

/** GET /api/health — kaydedilmiş gerçek yanıtla aynı şekil (tests/fixtures/api/health.json). */
export const healthSchema = z.object({
  status: z.string(),
  mode: z.string(),
  trading_enabled: z.boolean(),
});

export type Health = z.infer<typeof healthSchema>;

/** GET /api/capabilities — tests/fixtures/api/capabilities.json. */
export const capabilitiesSchema = z.object({
  mode: z.string(),
  data_mode: z.string(),
  execution_mode: z.string(),
  trading_enabled: z.boolean(),
  features: z.object({
    preview: z.boolean(),
    historical_import: z.boolean(),
    testnet: z.boolean(),
  }),
});

export type Capabilities = z.infer<typeof capabilitiesSchema>;

/** GET /api/system/status — tests/fixtures/api/system-status.json. */
export const systemStatusSchema = z.object({
  data: z.object({
    status: z.string(),
    data_dir: z.object({
      path: z.string(),
      exists: z.boolean(),
    }),
    disk: z.object({
      free_bytes: z.number(),
      total_bytes: z.number(),
    }),
    backups: z.object({
      count: z.number(),
      latest_created_us: z.number().nullable(),
    }),
  }),
});

export type SystemStatus = z.infer<typeof systemStatusSchema>;

/**
 * Backend v2 hataları (`application/problem+json`).
 * tests/fixtures/api/v2-bots-preview-422.json — gerçek 422 yanıtı.
 */
export const problemSchema = z.object({
  type: z.string().optional(),
  title: z.string().optional(),
  status: z.number().optional(),
  detail: z.string().optional(),
  code: z.string().optional(),
  errors: z
    .array(z.object({ field: z.string(), code: z.string() }))
    .optional(),
});

export type ProblemDetails = z.infer<typeof problemSchema>;

/** GET /api/risk/canary — tests/fixtures/api/risk-canary.json. */
export const canarySchema = z.object({
  data: z.object({
    verdict: z.string(),
    reasons: z.array(z.string()),
    kill_switch_engaged: z.boolean(),
    approval_present: z.boolean(),
    spec_status: z.string(),
    paper_fill_count: z.number(),
    observed_at: z.string(),
  }),
});

export type Canary = z.infer<typeof canarySchema>;

/** Tek landmark: GET /api/events satırı ve SSE /api/stream `data` yükü. */
export const landmarkSchema = z.object({
  seq: z.number(),
  kind: z.string(),
  ref: z.string(),
  summary: z.string(),
  time_us: z.number(),
});

export type Landmark = z.infer<typeof landmarkSchema>;

/** GET /api/events - tests/fixtures/api/events.json. */
export const eventsSchema = z.object({
  data: z.object({
    events: z.array(landmarkSchema),
  }),
});

export type Events = z.infer<typeof eventsSchema>;

/**
 * GET /api/notifications/state ve POST /api/notifications/read —
 * tests/fixtures/api/notifications-state.json, notifications-read.json.
 */
/** GET /api/notifications/telegram yanıtı — token asla dönmez. */
export const telegramStatusSchema = z.object({
  vault: z.string(),
  configured: z.boolean(),
  enabled: z.boolean(),
  chat_id: z.string(),
  cursor_seq: z.number(),
  last_error: z.string().nullable(),
});

export type TelegramStatus = z.infer<typeof telegramStatusSchema>;

export const telegramStatusEnvelopeSchema = z.object({ data: telegramStatusSchema });

export type TelegramStatusEnvelope = z.infer<typeof telegramStatusEnvelopeSchema>;

export const telegramTestEnvelopeSchema = z.object({ data: z.object({ message_id: z.number() }) });

export type TelegramTestEnvelope = z.infer<typeof telegramTestEnvelopeSchema>;

export const notificationStateSchema = z.object({
  data: z.object({
    last_seen_seq: z.number(),
    unread_count: z.number(),
  }),
});

export type NotificationState = z.infer<typeof notificationStateSchema>;

/**
 * GET /api/public/exchange-symbols — tests/fixtures/api/exchange-symbols.json
 * (tam yanıt) ve exchange-symbols-sample.json (ilk 50 kayıt).
 */
export const exchangeSymbolsSchema = z.object({
  environment: z.string(),
  symbols: z.array(
    z.object({
      symbol: z.string(),
      status: z.string(),
      base_asset: z.string(),
      quote_asset: z.string(),
    }),
  ),
  count: z.number(),
  observed_at_us: z.number(),
  read_only: z.boolean(),
  credential_required: z.boolean(),
});

export type ExchangeSymbols = z.infer<typeof exchangeSymbolsSchema>;

/**
 * DCA strateji gövdesi — v2-bots-created.json `data.strategy`.
 * Sayılar ondalık metindir; `max_active_safety_orders: null` sınırsızdır.
 */
export const dcaStrategySchema = z.object({
  symbol: z.string(),
  base_order: z.string(),
  safety_order: z.string(),
  max_safety_orders: z.number(),
  max_active_safety_orders: z.number().nullable(),
  price_deviation: z.string(),
  safety_order_volume_scale: z.string(),
  safety_order_step_scale: z.string(),
  take_profit: z.string(),
  stop_loss: z.string().nullable(),
  // Eski kayitlarda yoktur; okuma sirasinda acik varsayilanir.
  direction: z.enum(["LONG", "SHORT"]).default("LONG"),
  market_type: z.enum(["SPOT", "FUTURES"]).default("SPOT"),
  leverage: z.number().nullable().default(null),
  cooldown_seconds: z.number().default(0),
  min_price: z.string().nullable().default(null),
  max_price: z.string().nullable().default(null),
  // Eski kayitlarda yoktur; null = tek sembol (sembol alani gecerlidir).
  symbols: z.array(z.string()).nullable().default(null),
  max_active_deals: z.number().nullable().default(null),
  // G4-a: null = her deal kendi TP'sinde kapanir.
  combined_take_profit: z.string().nullable().default(null),
  // F09a: null = sabit TP cikisi (eski kayitlarda yoktur).
  trailing_take_profit: z.string().nullable().default(null),
});

export type DcaStrategy = z.infer<typeof dcaStrategySchema>;

/** Grid strateji gövdesi — grid bot kaydı `data.strategy`. */
export const gridBotStrategySchema = z.object({
  symbol: z.string(),
  mode: z.enum(["ARITHMETIC", "GEOMETRIC"]).default("ARITHMETIC"),
  lower_price: z.string(),
  upper_price: z.string(),
  interval_count: z.number(),
  fee_rate: z.string().default("0.001"),
  stop_loss_price: z.string().nullable().default(null),
  take_profit_pct: z.string().nullable().default(null),
  trailing_up_pct: z.string().nullable().default(null),
  trailing_down_pct: z.string().nullable().default(null),
});

export type GridBotStrategy = z.infer<typeof gridBotStrategySchema>;

/**
 * Futures grid strateji gövdesi. `direction`/`leverage` bilinçli olarak
 * varsayılansızdır: union ayrımı bu iki zorunlu alana dayanır.
 */
export const futuresGridBotStrategySchema = z.object({
  symbol: z.string(),
  direction: z.enum(["LONG", "SHORT"]),
  mode: z.enum(["ARITHMETIC", "GEOMETRIC"]).default("ARITHMETIC"),
  lower_price: z.string(),
  upper_price: z.string(),
  interval_count: z.number(),
  leverage: z.number(),
  fee_rate: z.string().default("0.0005"),
  stop_loss_price: z.string().nullable().default(null),
  take_profit_pct: z.string().nullable().default(null),
  trailing_up_pct: z.string().nullable().default(null),
  trailing_down_pct: z.string().nullable().default(null),
});

export type FuturesGridBotStrategy = z.infer<typeof futuresGridBotStrategySchema>;

export const botStrategySchema = z.union([
  dcaStrategySchema,
  futuresGridBotStrategySchema,
  gridBotStrategySchema,
]);

export type BotStrategy = z.infer<typeof botStrategySchema>;

/** Strateji ayrımı: grid gövdelerinde `lower_price` vardır, DCA'da yoktur. */
export function isGridStrategy(
  strategy: BotStrategy,
): strategy is GridBotStrategy | FuturesGridBotStrategy {
  return "lower_price" in strategy;
}

/** Spot/futures grid ayrımı: futures gövdelerinde `leverage` vardır. */
export function isFuturesGridStrategy(
  strategy: BotStrategy,
): strategy is FuturesGridBotStrategy {
  return "lower_price" in strategy && "leverage" in strategy;
}

/** POST /api/v2/grid-bots/preview yanıtı. */
export const gridPreviewSchema = z.object({
  symbol: z.string(),
  reference_price: z.string(),
  entry_position: z.enum(["BELOW", "WITHIN", "ABOVE"]),
  levels: z.array(z.string()),
  interval_count: z.number(),
  investment_quote: z.string(),
  quote_per_grid: z.string(),
  base_step_size: z.string(),
  fee_rate: z.string(),
  within_min_notional: z.boolean(),
  stop_loss_price: z.string().nullable(),
  take_profit_pct: z.string().nullable(),
  trailing_up_pct: z.string().nullable(),
  trailing_down_pct: z.string().nullable(),
});

export type GridPreview = z.infer<typeof gridPreviewSchema>;

export const gridPreviewEnvelopeSchema = z.object({ data: gridPreviewSchema });

export type GridPreviewEnvelope = z.infer<typeof gridPreviewEnvelopeSchema>;

/** POST /api/v2/futures-grid-bots/preview yanıtı. */
export const futuresGridPreviewSchema = z.object({
  symbol: z.string(),
  direction: z.string(),
  leverage: z.number(),
  reference_price: z.string(),
  entry_position: z.enum(["BELOW", "WITHIN", "ABOVE"]),
  levels: z.array(z.string()),
  interval_count: z.number(),
  investment_quote: z.string(),
  quote_per_grid: z.string(),
  notional_per_grid: z.string(),
  base_step_size: z.string(),
  fee_rate: z.string(),
  within_min_notional: z.boolean(),
  stop_loss_price: z.string().nullable(),
  take_profit_pct: z.string().nullable(),
  trailing_up_pct: z.string().nullable(),
  trailing_down_pct: z.string().nullable(),
});

export type FuturesGridPreview = z.infer<typeof futuresGridPreviewSchema>;

export const futuresGridPreviewEnvelopeSchema = z.object({ data: futuresGridPreviewSchema });

export type FuturesGridPreviewEnvelope = z.infer<typeof futuresGridPreviewEnvelopeSchema>;

/** GET /api/v2/bots/{id}/grid yanıtı. */
export const gridFillSchema = z.object({
  fill_id: z.string(),
  side: z.string(),
  price: z.string(),
  base_quantity: z.string(),
});

export type GridFill = z.infer<typeof gridFillSchema>;

export const gridStateSchema = z.object({
  grid_status: z.string(),
  entry_price: z.string().nullable(),
  last_price: z.string().nullable(),
  levels: z.array(z.string()),
  pending: z.array(z.string()),
  locked_quote: z.array(z.string()),
  locked_base: z.array(z.string()),
  quote_reserve: z.string(),
  base_free: z.string(),
  cycles_closed: z.number(),
  realized_profit_quote: z.string(),
  fees_paid_quote: z.string(),
  equity_at_last: z.string().nullable(),
  fills_recent: z.array(gridFillSchema),
  trailing_shifts: z.number(),
  last_bar_open_us: z.number().nullable(),
  updated_at_us: z.number().nullable(),
});

export type GridState = z.infer<typeof gridStateSchema>;

export const gridStateEnvelopeSchema = z.object({ data: gridStateSchema });

export type GridStateEnvelope = z.infer<typeof gridStateEnvelopeSchema>;

/** GET /api/v2/bots/{id}/grid yanıtı (futures grid botu). */
export const futuresGridFillSchema = z.object({
  fill_id: z.string(),
  side: z.string(),
  price: z.string(),
  quantity: z.string(),
});

export type FuturesGridFill = z.infer<typeof futuresGridFillSchema>;

export const futuresGridLotSchema = z.object({
  interval: z.number(),
  quantity: z.string(),
  entry_price: z.string(),
  locked_margin: z.string(),
});

export type FuturesGridLot = z.infer<typeof futuresGridLotSchema>;

export const futuresGridStateSchema = z.object({
  grid_status: z.string(),
  direction: z.string(),
  leverage: z.number(),
  entry_price: z.string().nullable(),
  last_price: z.string().nullable(),
  levels: z.array(z.string()),
  pending: z.array(z.string()),
  locked_margin: z.array(z.string()),
  wallet_free: z.string(),
  open_lots: z.array(futuresGridLotSchema),
  cycles_closed: z.number(),
  realized_gross_pnl: z.string(),
  fees_paid_quote: z.string(),
  funding_cashflow: z.string(),
  funding_events_count: z.number(),
  equity_at_last: z.string().nullable(),
  fills_recent: z.array(futuresGridFillSchema),
  trailing_shifts: z.number(),
  liq_estimate_price: z.string().nullable(),
  liq_estimate_tier: z.string().nullable(),
  last_bar_open_us: z.number().nullable(),
  updated_at_us: z.number().nullable(),
});

export type FuturesGridState = z.infer<typeof futuresGridStateSchema>;

/**
 * Grid durum zarfı, spot+futures. Futures önce denenir: spot gövdede
 * `direction`/`leverage` yoktur, futures gövde spot şemaya uyar ama
 * alan kaybederdi.
 */
export const anyGridStateEnvelopeSchema = z.object({
  data: z.union([futuresGridStateSchema, gridStateSchema]),
});

export type AnyGridStateEnvelope = z.infer<typeof anyGridStateEnvelopeSchema>;

/** Spot/futures durum ayrımı. */
export function isFuturesGridState(
  state: FuturesGridState | GridState,
): state is FuturesGridState {
  return "direction" in state;
}

/** POST /api/v2/bots/preview — v2-preview-{dengeli,sl}.json. */
export const dealPlanSchema = z.object({
  symbol: z.string(),
  reference_price: z.string(),
  base_order: z.object({ price: z.string(), qty: z.string(), amount: z.string() }),
  safety_orders: z.array(
    z.object({
      price: z.string(),
      qty: z.string(),
      amount: z.string(),
      index: z.number(),
      deviation_percent: z.string(),
    }),
  ),
  required_funds: z.string(),
  orders_total: z.string(),
  estimated_fees: z.string(),
  budget: z.string(),
  within_budget: z.boolean(),
  price_coverage_percent: z.string(),
  average_price_all_filled: z.string(),
  take_profit_price: z.string().nullable(),
  stop_loss_price_initial: z.string().nullable(),
  // Multi-pair onizlemede dolar; null = tek sembol.
  symbols: z.array(z.string()).nullable().default(null),
  total_required_funds: z.string().nullable().default(null),
  within_total_budget: z.boolean().nullable().default(null),
});

export type DealPlan = z.infer<typeof dealPlanSchema>;

export const dealPlanEnvelopeSchema = z.object({ data: dealPlanSchema });

export type DealPlanEnvelope = z.infer<typeof dealPlanEnvelopeSchema>;

/** v2 bot kaydı — v2-bots-created.json / v2-bots-get.json `data`. */
export const botSchema = z.object({
  bot_id: z.string(),
  name: z.string(),
  type: z.string(),
  mode: z.string(),
  status: z.string(),
  status_reason: z.string().nullable(),
  symbol: z.string(),
  budget: z.string(),
  strategy: botStrategySchema,
  revision: z.number(),
  created_at_us: z.number(),
  updated_at_us: z.number(),
  archived: z.boolean(),
});

export type Bot = z.infer<typeof botSchema>;

export const botEnvelopeSchema = z.object({ data: botSchema });

export type BotEnvelope = z.infer<typeof botEnvelopeSchema>;

/** POST /api/v2/bots/{id}/replay — geçmiş çalıştırma özeti. */
export const botReplaySchema = z.object({
  bars: z.number(),
  deals_opened: z.number(),
  deals_closed: z.number(),
  fills: z.number(),
  events: z.number(),
  first_bar_open_us: z.number(),
  last_bar_open_us: z.number(),
  symbols: z.array(z.string()),
  stopped: z.string().nullable(),
});

export type BotReplay = z.infer<typeof botReplaySchema>;

export const botReplayEnvelopeSchema = z.object({ data: botReplaySchema });

export type BotReplayEnvelope = z.infer<typeof botReplayEnvelopeSchema>;

/** GET /api/v2/bots — v2-bots.json (boş) ve v2-bots-list-one.json. */
export const botsSchema = z.object({
  data: z.array(botSchema),
});

export type Bots = z.infer<typeof botsSchema>;

/** GET /api/v2/bots/{id}/stats `data.active_deal` — v2-bot-stats-active.json. */
export const activeDealSchema = z.object({
  deal: z.number(),
  started_at_us: z.number(),
  safety_orders_filled: z.number(),
  max_safety_orders: z.number(),
  qty: z.string(),
  cost: z.string(),
  average_price: z.string(),
  mark_price: z.string().nullable(),
  unrealized_profit: z.string().nullable(),
  unrealized_percent: z.string().nullable(),
  take_profit_price: z.string().nullable(),
  next_safety_order_price: z.string().nullable(),
});

export type ActiveDeal = z.infer<typeof activeDealSchema>;

/** GET /api/v2/bots/{id}/stats — v2-bot-stats-{empty,active}.json. */
export const botStatsSchema = z.object({
  total_profit: z.string(),
  roi_percent: z.string(),
  deals_completed: z.number(),
  winning_deals: z.number(),
  win_rate_percent: z.string().nullable(),
  average_deal_profit: z.string().nullable(),
  average_deal_duration_us: z.number().nullable(),
  stop_loss_deals: z.number(),
  active_deal: activeDealSchema.nullable(),
  last_bar_open_us: z.number().nullable(),
});

export type BotStats = z.infer<typeof botStatsSchema>;

export const botStatsEnvelopeSchema = z.object({ data: botStatsSchema });

export type BotStatsEnvelope = z.infer<typeof botStatsEnvelopeSchema>;

export const closeReasonSchema = z.enum(["TAKE_PROFIT", "STOP_LOSS", "MANUAL_CLOSE", "CANCELLED"]);

export type CloseReason = z.infer<typeof closeReasonSchema>;

/** GET /api/v2/bots/{id}/deals `data[]` — v2-bot-deals.json (eskiden yeniye). */
export const botDealSchema = z.object({
  deal: z.number(),
  // Eski kayitlarda yoktur; null = botun tek sembolu.
  symbol: z.string().nullable().default(null),
  started_at_us: z.number(),
  closed_at_us: z.number().nullable(),
  safety_orders_filled: z.number(),
  manual_orders_filled: z.number(),
  profit: z.string().nullable(),
  close_reason: closeReasonSchema.nullable(),
  cumulative_profit: z.string().nullable(),
});

export type BotDeal = z.infer<typeof botDealSchema>;

export const botDealsEnvelopeSchema = z.object({ data: z.array(botDealSchema) });

export type BotDealsEnvelope = z.infer<typeof botDealsEnvelopeSchema>;



/**
 * GET /api/v2/bots/{id}/events `data[]` — v2-bot-events.json (yeniden eskiye).
 * `kind` gevşek metindir (backend yeni tür eklerse yanıt çöpe gitmez);
 * bilinmeyen `detail` anahtarları düz gösterilir.
 */
export const botEventSchema = z.object({
  time_us: z.number(),
  kind: z.string(),
  detail: z.record(z.string(), z.union([z.string(), z.number(), z.null()])),
});

export type BotEvent = z.infer<typeof botEventSchema>;

export const botEventsEnvelopeSchema = z.object({ data: z.array(botEventSchema) });

export type BotEventsEnvelope = z.infer<typeof botEventsEnvelopeSchema>;

/** GET /api/v2/deals `data[]` — v2-deals-{active,closed}.json (yeniden eskiye). */
export const dealV2Schema = z.object({
  bot_id: z.string(),
  bot_name: z.string(),
  symbol: z.string(),
  mode: z.string(),
  deal: z.number(),
  started_at_us: z.number(),
  closed_at_us: z.number().nullable(),
  safety_orders_filled: z.number(),
  manual_orders_filled: z.number(),
  profit: z.string().nullable(),
  close_reason: closeReasonSchema.nullable(),
});

export type DealV2 = z.infer<typeof dealV2Schema>;

export const dealsEnvelopeSchema = z.object({ data: z.array(dealV2Schema) });

export type DealsEnvelope = z.infer<typeof dealsEnvelopeSchema>;

/** GET /api/v2/bots/{id}/deals/{seq} — v2-deal-detail-{open,closed}.json. */
export const dealDetailSchema = dealV2Schema.extend({
  duration_us: z.number().nullable(),
  fees: z.string().nullable(),
  gross_profit: z.string().nullable(),
  qty: z.string().nullable(),
  cost: z.string().nullable(),
  average_price: z.string().nullable(),
  mark_price: z.string().nullable(),
  unrealized_profit: z.string().nullable(),
  unrealized_percent: z.string().nullable(),
  take_profit_price: z.string().nullable(),
  next_safety_order_price: z.string().nullable(),
  cumulative_profit: z.string().nullable(),
  events: z.array(botEventSchema),
});

export type DealDetail = z.infer<typeof dealDetailSchema>;

export const dealDetailEnvelopeSchema = z.object({ data: dealDetailSchema });

export type DealDetailEnvelope = z.infer<typeof dealDetailEnvelopeSchema>;

/** POST /api/v2/backtests — backtest-btcusdt-1h-14d.json. */
export const backtestSummarySchema = z.object({
  net_profit: z.string(),
  roi_percent: z.string(),
  annualized_roi_percent: z.string(),
  final_equity: z.string(),
  deals_completed: z.number(),
  winning_deals: z.number(),
  win_rate_percent: z.string().nullable(),
  average_deal_profit: z.string(),
  average_deal_duration_us: z.number(),
  max_safety_orders_used: z.number(),
  max_drawdown_percent: z.string(),
  total_fees: z.string(),
  // Q1: kayitli eski sonuclarda yoktur; null = zararsiz/kapali dealsiz.
  profit_factor: z.string().nullable().default(null),
  sharpe_ratio_annualized: z.string().nullable(),
});

export type BacktestSummary = z.infer<typeof backtestSummarySchema>;

export const backtestResultSchema = z.object({
  symbol: z.string(),
  interval: z.string(),
  period_start_us: z.number(),
  period_end_us: z.number(),
  bar_count: z.number(),
  processed_bar_count: z.number(),
  status: z.string(),
  indeterminate_at_us: z.number().nullable(),
  budget: z.string(),
  data_source: z.string(),
  summary: backtestSummarySchema,
  open_deal: z
    .object({ unrealized: z.string(), cost: z.string(), qty: z.string() })
    .nullable(),
  deals: z.array(
    z.object({
      deal: z.number(),
      started_at_us: z.number(),
      closed_at_us: z.number().nullable(),
      safety_orders_filled: z.number(),
      profit: z.string().nullable(),
      entry_price: z.string().nullable().default(null),
      exit_price: z.string().nullable().default(null),
    }),
  ),
  safety_order_usage: z.array(
    z.object({ safety_orders_filled: z.number(), deals: z.number() }),
  ),
  equity_curve: z.array(z.object({ time_us: z.number(), equity: z.string() })),
  // Q1: kosulan barlarin kapanislari; eski kayitta yoksa grafik gizlenir.
  price_curve: z.array(z.object({ time_us: z.number(), close: z.string() })).default([]),
  drawdown_curve: z.array(
    z.object({ time_us: z.number(), drawdown_percent: z.string() }),
  ),
  monthly_returns: z.array(
    z.object({ month: z.string(), return_percent: z.string(), complete: z.boolean() }),
  ),
  assumptions: z.array(z.string()),
});

export type BacktestResult = z.infer<typeof backtestResultSchema>;

export const backtestEnvelopeSchema = z.object({ data: backtestResultSchema });

export type BacktestEnvelope = z.infer<typeof backtestEnvelopeSchema>;

/**
 * GET /api/public/tickers-24h — tests/fixtures/api/tickers-24h.json.
 * İstenen sırada, en fazla 50 sembol.
 */
export const tickers24hSchema = z.object({
  data: z.array(
    z.object({
      symbol: z.string(),
      last_price: z.string(),
      price_change_percent: z.string(),
      quote_volume: z.string(),
    }),
  ),
  observed_at_us: z.number(),
  read_only: z.boolean(),
  credential_required: z.boolean(),
});

export type Tickers24h = z.infer<typeof tickers24hSchema>;

/** GET /api/public/ticker-24h — tests/fixtures/api/ticker-24h-btcusdt.json. */
export const ticker24hSchema = z.object({
  environment: z.string(),
  symbol: z.string(),
  last_price: z.string(),
  price_change_percent: z.string(),
  quote_volume: z.string(),
  observed_at_us: z.number(),
  read_only: z.boolean(),
  credential_required: z.boolean(),
});

export type Ticker24h = z.infer<typeof ticker24hSchema>;

/** GET /api/public/klines — tests/fixtures/api/klines-btcusdt-1h-300.json. */
export const klinesSchema = z.object({
  data: z.object({
    symbol: z.string(),
    interval: z.string(),
    bars: z.array(
      z.object({
        bar_index: z.number(),
        open_time_us: z.number(),
        close_time_us: z.number(),
        open: z.string(),
        high: z.string(),
        low: z.string(),
        close: z.string(),
        base_volume: z.string(),
      }),
    ),
    last_bar_closed: z.boolean(),
    observed_at_us: z.number(),
    read_only: z.boolean(),
    credential_required: z.boolean(),
  }),
});

export type Klines = z.infer<typeof klinesSchema>;
export type KlineBar = Klines["data"]["bars"][number];

/** GET /api/public/depth — tests/fixtures/api/depth-btcusdt-20.json. */
export const depthSchema = z.object({
  data: z.object({
    symbol: z.string(),
    last_update_id: z.number(),
    bids: z.array(z.tuple([z.string(), z.string()])),
    asks: z.array(z.tuple([z.string(), z.string()])),
    observed_at_us: z.number(),
    read_only: z.boolean(),
    credential_required: z.boolean(),
  }),
});

export type Depth = z.infer<typeof depthSchema>;

/**
 * POST /api/indicators/sma ve /ema — ısınma noktaları `value: null` gelir.
 * tests/fixtures/api/indicators-{sma-20,ema-50}.json.
 */
export const seriesIndicatorSchema = z.object({
  data: z.object({
    points: z.array(
      z.object({
        index: z.number(),
        value: z.string().nullable(),
        exact: z.boolean(),
      }),
    ),
  }),
});

export type SeriesIndicator = z.infer<typeof seriesIndicatorSchema>;

/** POST /api/indicators/bollinger — indicators-bollinger-20-2.json. */
export const bollingerSchema = z.object({
  data: z.object({
    points: z.array(
      z.object({
        index: z.number(),
        middle: z.string().nullable(),
        middle_exact: z.boolean(),
        variance: z.string().nullable(),
        variance_exact: z.boolean(),
        upper: z.string().nullable(),
        lower: z.string().nullable(),
        percent_b: z.string().nullable(),
      }),
    ),
  }),
});

export type Bollinger = z.infer<typeof bollingerSchema>;

/** POST /api/indicators/macd — indicators-macd.json. */
export const macdSchema = z.object({
  data: z.object({
    points: z.array(
      z.object({
        index: z.number(),
        macd: z.string().nullable(),
        signal: z.string().nullable(),
        histogram: z.string().nullable(),
      }),
    ),
  }),
});

export type Macd = z.infer<typeof macdSchema>;

/** POST /api/indicators/stoch-rsi — indicators-stoch-rsi.json. */
export const stochRsiSchema = z.object({
  data: z.object({
    points: z.array(
      z.object({
        index: z.number(),
        rsi: z.string().nullable(),
        stoch_rsi: z.string().nullable(),
      }),
    ),
  }),
});

export type StochRsi = z.infer<typeof stochRsiSchema>;

/**
 * POST /api/risk/regime — risk-regime-50.json. `confidence` bir olasılık
 * değildir; yüzde olarak gösterilmez, düz metin taşınır.
 */
export const regimeSchema = z.object({
  data: z.object({
    state: z.string(),
    direction: z.string().nullable(),
    confidence: z.string(),
    adx: z.string().nullable(),
    plus_di: z.string().nullable(),
    minus_di: z.string().nullable(),
    bb_width: z.string().nullable(),
  }),
});

export type Regime = z.infer<typeof regimeSchema>;

/**
 * Eski uçların hata biçimi (`{"error":{...}}`, `application/json`).
 * tests/fixtures/api/kill-switch-422.json — gerçek 422 yanıtı.
 */
export const legacyErrorSchema = z.object({
  error: z.object({
    code: z.string().optional(),
    message: z.string(),
    fields: z.record(z.string(), z.string()).optional(),
    revision: z.number().optional(),
  }),
});

export type LegacyError = z.infer<typeof legacyErrorSchema>;

/**
 * GET /api/public/symbol-rules — symbol-rules-{btcusdt,btcusdc}.json.
 * Bot kur düğmesinin tek kural kaynağıdır; istemci USDT kontrolü yapmaz.
 */
export const symbolRulesSchema = z.object({
  data: z.object({
    symbol: z.string(),
    status: z.string(),
    base_asset: z.string(),
    quote_asset: z.string(),
    tick: z.string(),
    qty_step: z.string(),
    min_qty: z.string(),
    min_notional: z.string(),
    bot_supported: z.boolean(),
    bot_unsupported_reason: z.string().nullable(),
  }),
});

export type SymbolRules = z.infer<typeof symbolRulesSchema>;

/**
 * GET /api/testnet/account — OpenAPI `BinanceTestnetAccountResponse`
 * modelinden. Canlıda kimlik yok: 409 `TESTNET_CREDENTIAL_NOT_CONFIGURED`
 * döner (testnet-account-409.json).
 */
export const testnetAccountSchema = z.object({
  environment: z.string(),
  account_type: z.string(),
  can_trade: z.boolean(),
  can_withdraw: z.boolean(),
  can_deposit: z.boolean(),
  permissions: z.array(z.string()),
  update_time_ms: z.number(),
  balances_count: z.number(),
  balances: z.array(
    z.object({ asset: z.string(), free: z.string(), locked: z.string() }),
  ),
  response_sha256: z.string(),
  observed_at_us: z.number(),
  read_only: z.boolean(),
  credential_required: z.boolean(),
});

export type TestnetAccount = z.infer<typeof testnetAccountSchema>;

/** GET /api/testnet/open-orders — OpenAPI `BinanceTestnetOpenOrdersResponse`. */
export const testnetOrdersSchema = z.object({
  environment: z.string(),
  orders: z.array(
    z.object({
      symbol: z.string(),
      order_id: z.number(),
      client_order_id: z.string(),
      side: z.string(),
      type: z.string(),
      status: z.string(),
      price: z.string(),
      orig_qty: z.string(),
      executed_qty: z.string(),
      time_ms: z.number(),
      update_time_ms: z.number(),
    }),
  ),
  count: z.number(),
  read_only: z.boolean(),
  credential_required: z.boolean(),
});

export type TestnetOrders = z.infer<typeof testnetOrdersSchema>;

/** POST /api/risk/kill-switch — kill-switch-{on,off}.json. */
export const killSwitchSchema = z.object({
  data: z.object({ engaged: z.boolean() }),
});

export type KillSwitch = z.infer<typeof killSwitchSchema>;

/** POST /api/risk/explain — risk-explain-{empty,pair}.json. */
export const riskExplainSchema = z.object({
  data: z.object({
    blocked: z.boolean(),
    reasons: z.array(
      z.object({ code: z.string(), severity: z.string(), message: z.string() }),
    ),
  }),
});

export type RiskExplain = z.infer<typeof riskExplainSchema>;

/** GET /api/datasets — datasets.json. */
export const datasetsSchema = z.object({
  datasets: z.array(
    z.object({
      dataset_id: z.string(),
      dataset_type: z.string(),
      instrument: z.string(),
      interval: z.string(),
      period_start: z.string(),
      period_end: z.string(),
      status: z.string(),
      artifact: z
        .object({ sha256: z.string(), byte_size: z.number() })
        .nullable(),
    }),
  ),
  count: z.number(),
});

export type Datasets = z.infer<typeof datasetsSchema>;

const downloadJobSchema = z.object({
  job_id: z.string(),
  dataset_id: z.string(),
  status: z.string(),
  attempt: z.number(),
  max_attempts: z.number(),
  bytes_downloaded: z.number(),
  total_bytes: z.number().nullable(),
  cache_hit: z.boolean().nullable(),
  error_code: z.string().nullable(),
  error_message: z.string().nullable(),
});

export type DownloadJob = z.infer<typeof downloadJobSchema>;

/** POST /api/dataset-downloads — download-start.json. */
export const downloadStartSchema = z.object({ job: downloadJobSchema });

export type DownloadStart = z.infer<typeof downloadStartSchema>;

/** GET /api/dataset-downloads/{id} ve POST …/cancel — download-{status,cancel}.json. */
export const downloadJobResponseSchema = downloadJobSchema;

/** POST /api/admin/backup — backup-taken.json. */
export const backupTakenSchema = z.object({
  data: z.object({
    manifest: z.object({
      store: z.string(),
      backup_file: z.string(),
      manifest_file: z.string(),
      bytes: z.number(),
      sha256: z.string(),
      created_us: z.number(),
    }),
  }),
});

export type BackupTaken = z.infer<typeof backupTakenSchema>;

/** POST /api/admin/backup/verify — backup-verify.json. */
export const backupVerifySchema = z.object({
  data: z.object({
    backup_file: z.string(),
    verdict: z.string(),
    application_id: z.number(),
    user_version: z.number(),
  }),
});

export type BackupVerify = z.infer<typeof backupVerifySchema>;

/** GET /api/admin/backups — backups.json. */
export const backupsSchema = z.object({
  data: z.object({
    backups: z.array(
      z.object({
        backup_file: z.string(),
        bytes: z.number(),
        created_us: z.number(),
        manifest_file: z.string(),
        sha256: z.string(),
        store: z.string(),
      }),
    ),
  }),
});

export type Backups = z.infer<typeof backupsSchema>;

/** GET /api/v2/stats/portfolio/summary — v2-portfolio-summary.json. */
export const portfolioSummarySchema = z.object({
  total_value: z.string(),
  today_profit: z.string(),
  active_bots: z.number(),
  deployed_capital: z.string(),
});

export type PortfolioSummary = z.infer<typeof portfolioSummarySchema>;

export const portfolioSummaryEnvelopeSchema = z.object({ data: portfolioSummarySchema });

export type PortfolioSummaryEnvelope = z.infer<typeof portfolioSummaryEnvelopeSchema>;

/** GET /api/v2/stats/portfolio/equity — v2-portfolio-equity.json. */
export const equityPointSchema = z.object({
  time_us: z.number(),
  equity: z.string(),
  realized: z.string(),
  unrealized: z.string(),
});

export type EquityPoint = z.infer<typeof equityPointSchema>;

export const equityEnvelopeSchema = z.object({ data: z.array(equityPointSchema) });

export type EquityEnvelope = z.infer<typeof equityEnvelopeSchema>;

/** GET /api/v2/stats/portfolio/daily-profit — v2-portfolio-daily.json. */
export const dailyProfitSchema = z.object({
  day_start_us: z.number(),
  profit: z.string(),
});

export type DailyProfit = z.infer<typeof dailyProfitSchema>;

export const dailyProfitEnvelopeSchema = z.object({ data: z.array(dailyProfitSchema) });

export type DailyProfitEnvelope = z.infer<typeof dailyProfitEnvelopeSchema>;

/** GET /api/v2/stats/portfolio/by-bot — v2-portfolio-by-bot.json. */
export const botProfitRowSchema = z.object({
  bot_id: z.string(),
  bot_name: z.string(),
  profit: z.string(),
  deals_completed: z.number(),
});

export type BotProfitRow = z.infer<typeof botProfitRowSchema>;

export const byBotEnvelopeSchema = z.object({ data: z.array(botProfitRowSchema) });

export type ByBotEnvelope = z.infer<typeof byBotEnvelopeSchema>;

/** GET /api/v2/stats/portfolio/by-pair — v2-portfolio-by-pair.json. */
export const pairProfitRowSchema = z.object({
  symbol: z.string(),
  profit: z.string(),
  deals_completed: z.number(),
  bots: z.number(),
});

export type PairProfitRow = z.infer<typeof pairProfitRowSchema>;

export const byPairEnvelopeSchema = z.object({ data: z.array(pairProfitRowSchema) });

export type ByPairEnvelope = z.infer<typeof byPairEnvelopeSchema>;
