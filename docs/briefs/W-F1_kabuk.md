# muse — Görev W-F1: tasarım sistemi + uygulama kabuğu

Plan: `docs/PLAN_WEB.md` §4 (terminoloji), §5 (bilgi mimarisi), §6.8 (tasarım sistemi), §10 (kabul).
İşbölümü: yalnız bu görevi yap ve bana raporla. `STATE.md`, `TASK.md`, `docs/KARARLAR.md` ve `src/` (backend) değiştirilmez. `web/src/lib/decimal.ts` Claude'undur, değiştirme; kullan.

## W-F0 geri bildirimi (önce oku)
İskelet kabul edildi. Kod temiz; tsc, lint, test, build ve e2e'yi kendim çalıştırdım. **Ancak rapor kodla uyuşmuyordu:**
- Raporda `/api/v1/session-demo`, "cüzdan/oturum kartları", "localStorage fixture enjeksiyonu", `tests/unit/api/schemas.test.ts`, `home-open.png` ve `home-closed.png` geçiyordu. Hiçbiri projede yok.
- Bu raporda **yalnız gerçekten var olan dosyaları ve gerçekten çalıştırdığın komutların çıktısını** yaz.
- Rapora komut çıktılarını kopyala: son satırlar yeterli, ama özetleme ya da yorumlama yapma.

Ek not: `tsconfig` hedefini ES2020'ye çektim, çünkü BigInt gerekiyordu.

## Yapılacaklar

### 1. Tasarım token'ları (`src/app/globals.css`)
- **Anlamsal renkler:**
  - `--profit` (yeşil)
  - `--loss` (kırmızı)
  - `--safety` (amber, safety order ve uyarı)
  - `--entry` (mavi, giriş ve ortalama)
  - `--accent` (tek vurgu)
  - nötr yüzeyler
- Koyu ve açık tema.
- Gradyan, parıltı ve gölge efekti yok.
- **Yazı tipleri:** Inter ve JetBrains Mono, **yerel** paketlerden gelir (`@fontsource-variable/inter`, `@fontsource-variable/jetbrains-mono`). `next/font/google` kullanılmaz; uygulama offline-first, build internetsiz de çalışmalı.
- Tüm sayılar `tabular-nums`.
- Renk sabitleri yalnız token bloğunda; bileşenlerde ham renk (`bg-emerald-600` gibi) yok. W-F0'daki geçici yeşil rozeti token'a taşı.

### 2. Bileşen kiti (`src/components/`)
- **Money / Price / Qty:** `DecimalString` alır, `formatDecimal` ile gösterir. Tanımsız değer "—".
- **PnL:** işaret ve renk `signOf`'tan; yüzde ve USDT varyantları.
- **StatCard:** etiket, değer, alt satır, isteğe bağlı mini grafik yuvası.
- **Badge varyantları:** `live`, `paper`, `testnet`, `running`, `paused`, `stopped`, `error`, `warn`.
- **ProgressToTarget:** "TP'ye %x".
  - Genişlik hesabı `src/lib/chart/` altında bir yardımcıda yapılır; `Number()` yalnız orada serbest.
  - Değer backend'in yüzde metni olarak gelir.
- **ChartCard:** başlık, zaman aralığı çipleri, grafik gövdesi, boş/yükleniyor/hata durumları.
- **DataTable:** `@tanstack/react-table`; sıralama, sayfalama, boş durum. Mobilde kart görünümüne düşer.
- **EmptyState:** davet cümlesi ve bir eylem. "Veri yok" gibi özür dili yok.
- **ConfirmDialog:** geri alınamaz eylemler için; gerekçe alanı isteğe bağlı.
- **Skeleton.**

### 3. Bileşen galerisi `/design`
- Yukarıdaki her bileşen örnek verilerle, her durumuyla (normal, boş, yükleniyor, hata, negatif ve pozitif PnL) görünür.
- Örnek veriler `DecimalString` metinleridir; bu sayfada backend çağrısı yok.

### 4. Uygulama kabuğu
- **Kenar menü, 6 öğe, sırayla:** Kontrol merkezi `/` · Botlar `/bots` · Deal'ler `/deals` · Backtest `/backtest` · Piyasa `/market` · Ayarlar `/settings`.
  - İkonlar `lucide-react`.
  - Aktif öğe belirgin.
  - Dar ekranda (<1024 px) menü açılır çekmeceye dönüşür.
- **Üst çubuk:**
  - **Mod rozeti:** `/api/capabilities` `execution_mode` alanından. SIMULATED → "Paper". Bilinmeyen değer → değerin kendisi + `warn` rozeti. Uydurma eşleme yok.
  - **Kill switch durumu:** `GET /api/risk/canary` yanıtından, salt okunur rozet. Alan adını fixture'dan al. Açma/kapama W-F8'de.
  - **Bağlantı noktası:** `/api/health` 15 sn'de bir; kopunca kırmızı ve ipucu metni.
  - **Bildirimler:** zil → `/api/events?limit=20` son olaylar listesi; boşsa EmptyState.
  - **Ctrl+K komut paleti:** menü sayfalarına git + parite ara (`/api/public/exchange-symbols`). Seçilen parite `/market/<SYMBOL>`'e gider.
  - **Tema ve dil geçişi** (TR/EN).
- **Sayfalar:** 6 rota da kabuğun içinde açılır. Her biri başlık ve dürüst bir EmptyState gösterir: "Bu ekran bir sonraki adımda geliyor" + ilgili açıklama. Sahte veri yok.
  - `/` sayfasındaki W-F0 bağlantı kartı Ayarlar > Sistem bölümüne taşınır.

### 5. API katmanı
- `ApiHttpError` genişletilecek: yanıt `application/problem+json` ise `code`, `detail` ve `errors[{field, code}]` okunur (backend v2 hataları bu biçimde). Arayüz hata metnini `detail`'den gösterir; ham istisna metni gösterilmez.
- `record:fixtures` listesine şunlar eklenir: `/api/risk/canary`, `/api/events?limit=20`, `/api/public/exchange-symbols` (bu dosya büyükse ilk 50 kayıt ayrı bir örnek dosyaya), `/api/v2/bots` ve bir v2 hata örneği.
  - v2 hata örneği için: `POST /api/v2/bots/preview`'a `{"budget":"1","strategy":{}}` gönder, 422 Problem Details yanıtını kaydet.
- `npm run gen:api` yeniden çalıştırılır; `/api/v2/*` tipleri `schema.d.ts`'te görünmeli.

### 6. Testler
- **Vitest:**
  - Money/PnL biçim ve renk sınıfı (pozitif, negatif, sıfır, "—").
  - Problem Details ayrıştırma (kaydedilmiş gerçek 422 yanıtıyla).
  - Mod rozeti eşlemesi.
  - Komut paleti filtreleme.
- **Playwright:**
  - Kabuk: 6 menü öğesi gezilir, her sayfa açılır.
  - Ctrl+K ile `BTCUSDT` aranır ve `/market/BTCUSDT`'ye gidilir.
  - axe kritik ihlal 0.
  - Görsel taban (`toHaveScreenshot`): `/design` koyu + açık tema, kabuk 1440 px + 390 px.
- **CI:** e2e işini ekle. Backend'i `uv run --frozen uvicorn dcabot.server.api:app --port 8000` ile arka planda başlat, sağlık kontrolünü bekle, sonra `npx playwright install --with-deps chromium` ve `test:e2e` çalıştır.

## Sınırlar
- İstemcide finansal hesap yok. Para, fiyat ve miktar yalnız `formatDecimal` ile gösterilir.
- `Number()` yalnız `src/lib/chart/**` altında.
- Backend'e dokunma; eksik ya da yanlış bir uç varsa bana yaz.
- Arşivdeki eski frontend ve qwen referans alınmaz.

## Rapor (bana)
1. Yeni ve değişen dosyaların **gerçek** listesi: `git status --short -- web .claude .github` çıktısını aynen yapıştır.
2. `npm run typecheck`, `lint`, `test`, `build`, `test:e2e` çıktılarının son satırları.
3. Ekran görüntüleri ve **dosya yolları**:
   - `/design` koyu ve açık
   - kabuk masaüstü ve mobil
   - komut paleti açık
   - backend kapalıyken üst çubuk
4. Plandan sapmalar, gerekçesiyle. Emin olmadığın noktayı sor.
