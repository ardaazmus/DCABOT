import { afterEach, describe, expect, it, vi } from "vitest";

import fixture422 from "../../../tests/fixtures/api/v2-bots-preview-422.json";
import { ApiHttpError, apiPost } from "./client";
import { botsSchema } from "./schemas";

describe("Problem Details", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("kaydedilmiş gerçek 422 yanıtını ayrıştırır, detail gösterir", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(fixture422), {
          status: 422,
          headers: { "content-type": "application/problem+json" },
        }),
      ),
    );
    const error = await apiPost(
      "/api/v2/bots/preview",
      { budget: "1", strategy: {} },
      botsSchema,
    ).catch((cause: unknown) => cause);
    expect(error).toBeInstanceOf(ApiHttpError);
    const httpError = error as ApiHttpError;
    expect(httpError.status).toBe(422);
    expect(httpError.problem?.code).toBe("REQUEST_VALIDATION_FAILED");
    expect(httpError.problem?.errors).toHaveLength(10);
    expect(httpError.problem?.errors?.[0]).toEqual({
      field: "strategy.symbol",
      code: "INVALID_REQUEST",
    });
    // Arayüzün göstereceği metin backend'in detail alanıdır.
    expect(httpError.message).toBe(fixture422.detail);
  });

  it("problem+json olmayan hatada problem tanımsız kalır", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response("patladı", {
          status: 500,
          headers: { "content-type": "text/plain" },
        }),
      ),
    );
    const error = await apiPost("/api/v2/bots/preview", {}, botsSchema).catch(
      (cause: unknown) => cause,
    );
    expect(error).toBeInstanceOf(ApiHttpError);
    expect((error as ApiHttpError).problem).toBeUndefined();
  });
});
