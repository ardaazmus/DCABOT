import { afterEach, describe, expect, it, vi } from "vitest";

import healthFixture from "../../../tests/fixtures/api/health.json";
import {
  ApiContractError,
  ApiNetworkError,
  apiGet,
  apiPost,
} from "./client";
import { healthSchema } from "./schemas";

function mockJsonResponse(data: unknown) {
  return {
    ok: true,
    status: 200,
    json: async () => data,
  } as Response;
}

describe("api istemcisi", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("geçerli kayıtlı yanıtı doğrular ve döndürür", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(mockJsonResponse(healthFixture)),
    );
    const result = await apiGet("/api/health", healthSchema);
    expect(result).toEqual(healthFixture);
    expect(fetch).toHaveBeenCalledWith("/api/health", { method: "GET" });
  });

  it("bozuk yanıtta ApiContractError fırlatır, sessiz geçmez", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        mockJsonResponse({ status: "ok", trading_enabled: "evet" }),
      ),
    );
    const error = await apiGet("/api/health", healthSchema).catch(
      (cause: unknown) => cause,
    );
    expect(error).toBeInstanceOf(ApiContractError);
    expect((error as ApiContractError).path).toBe("/api/health");
  });

  it("ağ hatasında ApiNetworkError fırlatır", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("fetch failed")),
    );
    const error = await apiPost("/api/health", {}, healthSchema).catch(
      (cause: unknown) => cause,
    );
    expect(error).toBeInstanceOf(ApiNetworkError);
    expect((error as ApiNetworkError).path).toBe("/api/health");
  });
});
