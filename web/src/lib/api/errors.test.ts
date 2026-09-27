import { afterEach, describe, expect, it, vi } from "vitest";

import killSwitch422 from "../../../tests/fixtures/api/kill-switch-422.json";
import testnet409 from "../../../tests/fixtures/api/testnet-account-409.json";
import { ApiHttpError, apiGet, apiPost } from "./client";
import { killSwitchSchema, testnetAccountSchema } from "./schemas";

describe("hata biçimleri", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("eski {error} biçimini ayrıştırır, message gösterir", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(killSwitch422), {
          status: 422,
          headers: { "content-type": "application/json" },
        }),
      ),
    );
    const error = await apiPost(
      "/api/risk/kill-switch",
      { engaged: true },
      killSwitchSchema,
    ).catch((cause: unknown) => cause);
    expect(error).toBeInstanceOf(ApiHttpError);
    const httpError = error as ApiHttpError;
    expect(httpError.status).toBe(422);
    expect(httpError.problem).toBeUndefined();
    expect(httpError.legacy?.error.code).toBe("validation_error");
    expect(httpError.legacy?.error.fields?.reason).toContain("1..200");
    expect(httpError.message).toBe(killSwitch422.error.message);
  });

  it("409 problem kodunu taşır", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(testnet409), {
          status: 409,
          headers: { "content-type": "application/problem+json" },
        }),
      ),
    );
    const error = await apiGet("/api/testnet/account", testnetAccountSchema).catch(
      (cause: unknown) => cause,
    );
    expect(error).toBeInstanceOf(ApiHttpError);
    const httpError = error as ApiHttpError;
    expect(httpError.status).toBe(409);
    expect(httpError.problem?.code).toBe("TESTNET_CREDENTIAL_NOT_CONFIGURED");
    expect(httpError.legacy).toBeUndefined();
  });
});
