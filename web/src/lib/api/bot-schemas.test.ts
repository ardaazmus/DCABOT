import { describe, expect, it } from "vitest";

import { ApiHttpError, ApiNetworkError } from "./client";
import { shouldRetryPreview } from "./queries";

import archive200 from "../../../tests/fixtures/api/v2-bots-archive-200.json";
import archive409 from "../../../tests/fixtures/api/v2-bots-archive-409-revision.json";
import created from "../../../tests/fixtures/api/v2-bots-created.json";
import create422 from "../../../tests/fixtures/api/v2-bots-create-422-budget.json";
import getFixture from "../../../tests/fixtures/api/v2-bots-get.json";
import listOne from "../../../tests/fixtures/api/v2-bots-list-one.json";
import pause409 from "../../../tests/fixtures/api/v2-bots-pause-409-transition.json";
import start409 from "../../../tests/fixtures/api/v2-bots-start-409.json";
import preview422Base from "../../../tests/fixtures/api/v2-preview-422-base-small.json";
import preview422Budget from "../../../tests/fixtures/api/v2-preview-422-budget.json";
import preview422Config from "../../../tests/fixtures/api/v2-preview-422-config.json";
import preview422Quote from "../../../tests/fixtures/api/v2-preview-422-quote.json";
import preview422Range from "../../../tests/fixtures/api/v2-preview-422-range.json";
import previewDengeli from "../../../tests/fixtures/api/v2-preview-dengeli.json";
import previewFalse from "../../../tests/fixtures/api/v2-preview-within-budget-false.json";
import previewSl from "../../../tests/fixtures/api/v2-preview-sl.json";
import {
  botEnvelopeSchema,
  botReplayEnvelopeSchema,
  botsSchema,
  dealPlanEnvelopeSchema,
  isGridStrategy,
  problemSchema,
} from "./schemas";

describe("v2 bot şemaları (gerçek fixture)", () => {
  it("önizleme Dengeli yanıtını doğrular", () => {
    const plan = dealPlanEnvelopeSchema.parse(previewDengeli).data;
    expect(plan.symbol).toBe("BTCUSDT");
    expect(plan.safety_orders).toHaveLength(6);
    expect(plan.safety_orders[0]?.index).toBe(1);
    expect(plan.within_budget).toBe(true);
    expect(plan.take_profit_price).not.toBeNull();
    expect(plan.stop_loss_price_initial).toBeNull();
  });

  it("dar bütçede within_budget false gelir", () => {
    const plan = dealPlanEnvelopeSchema.parse(previewFalse).data;
    expect(plan.within_budget).toBe(false);
    expect(plan.budget).toBe("10");
  });

  it("açık SL başlangıç fiyatını doldurur", () => {
    const plan = dealPlanEnvelopeSchema.parse(previewSl).data;
    expect(plan.stop_loss_price_initial).not.toBeNull();
  });

  it("bot oluşturma/okuma/arşiv yanıtlarını doğrular", () => {
    const fresh = botEnvelopeSchema.parse(created).data;
    expect(fresh.status).toBe("STOPPED");
    expect(fresh.revision).toBe(1);
    expect(fresh.archived).toBe(false);
    expect(fresh.strategy.symbol).toBe("BTCUSDT");
    expect(botEnvelopeSchema.parse(getFixture).data.bot_id).toBe(fresh.bot_id);
    expect(botsSchema.parse(listOne).data).toHaveLength(1);
    expect(botEnvelopeSchema.parse(archive200).data.archived).toBe(true);
  });

  it("eski strateji şekli yön/kapı defaults ile okunur", () => {
    const legacy = {
      ...created.data,
      strategy: {
        symbol: "BTCUSDT",
        base_order: "25",
        safety_order: "25",
        max_safety_orders: 6,
        max_active_safety_orders: 2,
        price_deviation: "1.5",
        safety_order_volume_scale: "1.5",
        safety_order_step_scale: "1.2",
        take_profit: "2",
        stop_loss: null,
      },
    };
    const parsed = botEnvelopeSchema.parse({ data: legacy }).data;
    expect(isGridStrategy(parsed.strategy)).toBe(false);
    if (isGridStrategy(parsed.strategy)) return;
    expect(parsed.strategy.direction).toBe("LONG");
    expect(parsed.strategy.market_type).toBe("SPOT");
    expect(parsed.strategy.leverage).toBeNull();
    expect(parsed.strategy.cooldown_seconds).toBe(0);
    expect(parsed.strategy.min_price).toBeNull();
    expect(parsed.strategy.max_price).toBeNull();
  });

  it("her 422 kodu field eşlemesiyle gelir", () => {
    const cases = [
      [preview422Base, "SECTOR_BASE_ORDER_TOO_SMALL", "strategy.base_order"],
      [preview422Quote, "SECTOR_QUOTE_UNSUPPORTED", "strategy.symbol"],
      [preview422Range, "SECTOR_FIELD_OUT_OF_RANGE", "strategy.price_deviation"],
      [preview422Budget, "SECTOR_FIELD_OUT_OF_RANGE", "budget"],
      [preview422Config, "SECTOR_CONFIG_INVALID", "strategy"],
      [create422, "SECTOR_BUDGET_TOO_LOW", "budget"],
    ] as const;
    for (const [fixture, code, field] of cases) {
      const problem = problemSchema.parse(fixture);
      expect(problem.code).toBe(code);
      expect(problem.errors).toEqual([{ field, code }]);
      expect(problem.detail).not.toBe("");
    }
  });

  it("önizleme yalnız geçici hataları dener", () => {
    const http = (status: number) => new ApiHttpError("/api/v2/bots/preview", status);
    expect(shouldRetryPreview(0, new ApiNetworkError("/api/v2/bots/preview", null))).toBe(true);
    expect(shouldRetryPreview(0, http(502))).toBe(true);
    expect(shouldRetryPreview(1, http(500))).toBe(true);
    expect(shouldRetryPreview(2, http(502))).toBe(false);
    expect(shouldRetryPreview(0, http(422))).toBe(false);
    expect(shouldRetryPreview(0, http(409))).toBe(false);
    expect(shouldRetryPreview(0, new Error("başka"))).toBe(false);
  });

  it("eylem 409'ları kodlarıyla gelir", () => {
    expect(problemSchema.parse(start409).code).toBe("BOT_RUNNER_UNAVAILABLE");
    expect(problemSchema.parse(archive409).code).toBe("BOT_REVISION_CONFLICT");
    expect(problemSchema.parse(pause409).code).toBe("BOT_TRANSITION_INVALID");
  });

  it("geçmiş çalıştırma özetini doğrular", () => {
    const parsed = botReplayEnvelopeSchema.parse({
      data: {
        bars: 2880,
        deals_opened: 2,
        deals_closed: 1,
        fills: 0,
        events: 5,
        first_bar_open_us: 1789862400000000,
        last_bar_open_us: 1790035140000000,
        symbols: ["BTCUSDT"],
        stopped: null,
      },
    }).data;
    expect(parsed.bars).toBe(2880);
    expect(parsed.symbols).toEqual(["BTCUSDT"]);
    expect(parsed.stopped).toBeNull();
  });
});
