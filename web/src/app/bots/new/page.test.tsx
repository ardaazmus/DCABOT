import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NextIntlClientProvider } from "next-intl";
import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import previewDengeli from "../../../../tests/fixtures/api/v2-preview-dengeli.json";
import rulesUsdt from "../../../../tests/fixtures/api/symbol-rules-btcusdt.json";
import tr from "@/messages/tr.json";
import BotsNewPage from "@/app/bots/new/page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => new URLSearchParams("symbol=BTCUSDT"),
}));

const REQUIRED = (previewDengeli.data as { required_funds: string }).required_funds;

function renderWizard() {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input);
      let body: unknown = { environment: "test", symbols: [], count: 0, observed_at_us: 0, read_only: true, credential_required: false };
      if (url.includes("/api/public/symbol-rules")) body = rulesUsdt;
      else if (url.includes("/api/v2/bots/preview")) body = previewDengeli;
      return { ok: true, status: 200, json: async () => body } as Response;
    }),
  );
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <NextIntlClientProvider locale="tr" messages={tr} timeZone="Europe/Istanbul">
      <QueryClientProvider client={queryClient}>
        <BotsNewPage />
      </QueryClientProvider>
    </NextIntlClientProvider>,
  );
}

describe("kurulum formu (kayıtlı yanıtlar)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("?symbol= ile ön dolu gelir, Dengeli seçilidir, tüm bölümler görünür", async () => {
    renderWizard();
    const symbol = (await screen.findByTestId("wizard-symbol")) as HTMLInputElement;
    expect(symbol.value).toBe("BTCUSDT");
    const balanced = await screen.findByRole("radio", { name: "Dengeli" });
    expect(balanced.getAttribute("aria-checked")).toBe("true");
    // Tek sayfa: giriş + bütçe alanları aynı anda görünür.
    expect(screen.getByTestId("wizard-base-order")).toBeDefined();
    expect(screen.getByTestId("wizard-budget")).toBeDefined();
    expect(screen.getByTestId("wizard-create")).toBeDefined();
  });

  it("Gereken tutarı kullan: metin aynen kopyalanır", async () => {
    renderWizard();
    const budget = (await screen.findByTestId("wizard-budget")) as HTMLInputElement;
    fireEvent.change(budget, { target: { value: "10" } });
    // Önizleme 400 ms gecikmeyle gelir; kayıtlı yanıt kullanılır.
    const useRequired = await screen.findByRole("button", { name: "Gereken tutarı kullan" });
    fireEvent.click(useRequired);
    expect((screen.getByTestId("wizard-budget") as HTMLInputElement).value).toBe(REQUIRED);
  });
});
