import { expect, type APIRequestContext, type APIResponse, type Page } from "@playwright/test";

/**
 * Piyasa parite sayfasını açar ve grafik tuvalini bekler.
 *
 * e2e canlı Binance kullanır; tekil yukarı-akım istekleri düşebilir ve
 * ürün bu durumda dürüst-hata gösterir ("Bu parite bulunamadı") — bu
 * doğru ürün davranışıdır. Geçici aksaklıkla gerçek kırığı ayırt
 * etmek için hata görülürse sayfa BİR kez yenilenir; ikinci
 * denemede de grafik yoksa yüksek sesle düşer. Retry sayılmaz:
 * aynı koşul iki kez doğrulanır, sessiz geçme yoktur.
 */
export async function gotoMarketSymbol(page: Page, path: string): Promise<void> {
  for (let attempt = 1; attempt <= 2; attempt++) {
    if (attempt === 1) {
      await page.goto(path);
    } else {
      await page.reload();
    }
    const canvas = page.getByTestId("price-chart").locator("canvas").first();
    const honestError = page.getByText("Bu parite bulunamadı");
    await expect(canvas.or(honestError)).toBeVisible({ timeout: 20000 });
    if (await honestError.isVisible()) {
      if (attempt === 2) {
        throw new Error(
          `Piyasa sayfası iki denemede de dürüst-hata gösterdi (${path}); yukarı-akım ya da ürün kırık.`,
        );
      }
      continue;
    }
    await expect(canvas).toBeVisible({ timeout: 20000 });
    return;
  }
}

/**
 * Piyasa listesini açar ve ilk parite satırını bekler.
 * Yukarı-akım düşerse sayfa dürüst-hata gösterir ("Parite listesi
 * alınamadı."); aynı ayırt etme kuralı: BİR yenileme, sonra yüksek ses.
 */
export async function gotoMarketList(page: Page): Promise<void> {
  for (let attempt = 1; attempt <= 2; attempt++) {
    if (attempt === 1) {
      await page.goto("/market");
    } else {
      await page.reload();
    }
    const firstPair = page.getByRole("link", { name: "BTCUSDT" });
    const loadError = page.getByText("Parite listesi alınamadı.");
    await expect(firstPair.or(loadError)).toBeVisible({ timeout: 20000 });
    if (!(await loadError.isVisible())) {
      await expect(firstPair).toBeVisible({ timeout: 20000 });
      return;
    }
    if (attempt === 2) {
      throw new Error("Piyasa listesi iki denemede de alınamadı; yukarı-akım ya da ürün kırık.");
    }
  }
}

/**
 * Canlı yukarı-akım (Binance) gerektiren yazma istekleri: 502/503'te
 * BİR kez yinelenir, sonra yüksek sesle düşer (gotoMarketSymbol ile
 * aynı kural). 4xx/500 yinelenmez: ürün davranışıdır.
 */
export async function postWithUpstreamRetry(
  request: APIRequestContext,
  url: string,
  options: { data: unknown },
): Promise<APIResponse> {
  let response = await request.post(url, options);
  if (!response.ok() && (response.status() === 502 || response.status() === 503)) {
    response = await request.post(url, options);
  }
  expect(response.ok(), `POST ${url} -> ${response.status()}`).toBe(true);
  return response;
}
