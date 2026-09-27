# muse — Görev W-F0: `web/` iskeleti

Plan: `docs/PLAN_WEB.md` (§3 teknoloji, §10 kabul). Arşivdeki eski frontend ve qwen **referans alınmaz, kopyalanmaz**.
İşbölümü: yalnız bu görevi yap, bana raporla. `STATE.md`, `TASK.md`, `docs/KARARLAR.md`, `src/` (backend) değiştirilmez.

## Amaç
Boş ama uçtan uca çalışan bir Next.js uygulaması. Sonraki bütün ekranlar bunun üzerine kurulacak. Bu dilimde ekran tasarımı yok; yalnız altyapı ve backend bağlantısının kanıtı var.

## Yapılacaklar
1. **Proje:** `npx create-next-app@latest web --ts --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm`
   Next 16.3.x, React 19.3.x, Tailwind 4.3.x (2026-09-24 npm sürümleri). TypeScript `strict: true` ve `noUncheckedIndexedAccess: true`.
2. **Bağımlılıklar:**
   - Çalışma: `@tanstack/react-query`, `zustand`, `next-themes`, `next-intl`, `zod`, `lightweight-charts`, `recharts`
   - Geliştirme: `openapi-typescript`, `vitest`, `@vitejs/plugin-react`, `jsdom`, `@testing-library/react`, `@testing-library/jest-dom`, `fast-check`, `@playwright/test`, `@axe-core/playwright`
   - `npx shadcn@latest init` (varsayılan stil, CSS değişkenleri açık).
3. **Backend proxy:** `next.config.ts` içinde `/api/:path*` → `${DCABOT_API_URL ?? "http://127.0.0.1:8000"}/api/:path*` rewrite. Tarayıcı backend'e her zaman `/api/...` ile gider.
4. **Sağlayıcılar** (`src/app/providers.tsx`):
   - QueryClient: varsayılan `retry: 1`, `refetchOnWindowFocus: false`
   - ThemeProvider: koyu varsayılan, açık tema var
   - next-intl: `tr` varsayılan, `en` ikinci dil; mesajlar `src/messages/{tr,en}.json`
5. **API katmanı** (`src/lib/api/`):
   - `npm run gen:api`: `openapi-typescript http://127.0.0.1:8000/openapi.json -o src/lib/api/schema.d.ts`. Üretilen dosya commit edilir.
   - `client.ts`: `apiGet<T>(path, schema)` / `apiPost<T>(path, body, schema)`. Her yanıt sınırda zod ile doğrulanır; doğrulama başarısızsa tipli bir `ApiContractError` fırlatılır. **Sessiz geçiş yok.**
   - `npm run record:fixtures`: çalışan backend'den `GET /api/health`, `/api/capabilities`, `/api/system/status` yanıtlarını `tests/fixtures/api/*.json` dosyasına kaydeden betik. Testler **yalnız bu kaydedilmiş gerçek yanıtları** kullanır; elle fixture yazmak yasak.
6. **Sayı kuralı:**
   - `src/lib/decimal.ts` dosyasını **Claude yazacak**; sen oluşturma. Para ve fiyat biçimlendirmesi bu dosyadan gelecek.
   - ESLint: `parseFloat` yasak. `Number(` çağrısı yalnız `src/lib/chart/**` altında serbest (`no-restricted-syntax` + override).
7. **Tek kanıt sayfası** `/`:
   - "Sistem bağlantısı" kartı: `/api/health` ve `/api/capabilities` sonuçları.
   - Bağlı ise yeşil "Bağlı" rozeti + mod bilgisi (`execution_mode`, `data_mode`).
   - Backend kapalıysa dürüst hata metni + "Tekrar dene" butonu.
   - Tasarım yok, shadcn `Card` + `Badge` yeterli.
8. **Test altyapısı:**
   - Vitest (jsdom): client zod doğrulaması için 3 test (geçerli fixture, bozuk yanıt → `ApiContractError`, ağ hatası).
   - Playwright: `webServer` `next dev` başlatır; backend 8000'de çalışıyor kabul edilir. 1 e2e: `/` açılır, "Bağlı" görünür, axe kritik ihlal 0, ekran görüntüsü alınır.
9. **Script'ler:** `dev`, `build`, `typecheck` (`tsc --noEmit`), `lint`, `test`, `test:e2e`, `gen:api`, `record:fixtures`.
10. **Çalıştırma:**
    - `.claude/launch.json`'a `dcabot-web` ekle: `npm --prefix web run dev`, port 3000.
    - CI (`.github/workflows/quality.yml`) mevcut Python adımlarından sonra: setup-node 22 (cache `web/package-lock.json`), `npm ci --prefix web`, `typecheck`, `lint`, `test`, `build`.
    - e2e CI'a şimdi eklenmez (backend gerektiriyor; W-F1'de eklenecek).

## Sınırlar
- İstemcide finansal hesap yok.
- Backend dosyalarına dokunma. Bir uç eksik ya da yanlışsa bana yaz.
- Arşivdeki koddan kopyalama yok.

## Rapor (bana)
1. Oluşan dosya ağacı (`web/src` iki seviye) ve `package.json` bağımlılık sürümleri.
2. `npm run typecheck`, `lint`, `test`, `build`, `test:e2e` çıktı özetleri (geçen/toplam).
3. `/` sayfasının ekran görüntüsü: backend açıkken ve kapalıyken iki ayrı görüntü.
4. Plandan saptığın her nokta, gerekçesiyle. Emin olmadığın maddeyi atlama, sor.
