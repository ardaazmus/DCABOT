# Faz W (web arayüzü) — SONUÇ (Muse, 2026-09-26)

Önceki (YOL_HARITASI'ndan): W-F9a + W-F5b (3×62/62 e2e) ·
W-B4 + W-F6 + W-B5 (e2e 65/65). Bu dosya W-F7 ile açıldı.

## W-F7 — kontrol merkezi `/` (2026-09-26, Muse)
Kapsam: KPI kartları, equity alan grafiği, günlük kâr çubukları,
bot/parite halkası, aktif deal'ler. Veri yalnız W-B5 uçlarından
(summary/equity/daily-profit/by-bot/by-pair); finansal hesap
UI'da yok, çekirdek tek doğruluk kaynağı.
- Şemalar + sorgular + dashboard bileşenleri + TR/EN i18n.
- Iraksak çubuklar korundu (kazanç/kayıp halkası ertelendi);
  TP ilerleme çubuğu ertelendi.
- Stabilizasyon: sabit "E2E panel" bot adı (Date.now kaldırıldı),
  shell-1440 piksel tabanı → yapısal assertion, exact Paper
  locator'ları, liste h1 düzeltmesi.

Kanıt (LOCAL):
- checker 2232/2232 OK (1 skip) · vitest 200/200 (46 dosya) ·
  tsc temiz · e2e 67/67 temiz koşu.
- 4 tam koşuda 1 geçici dalgalanma (bots:135 arşiv; izole +
  dosya + tekrar koşuda yeşil, kod hatası değil).

Sınırlar: mainnet NO-GO; testnet mutation kapalı; review=NOT_RUN.

## W-B6 — SSE canlı akış `/api/stream` (2026-09-26, Muse)
Kapsam: replay (Last-Event-ID/sorgu) + canlı itme + 15 sn ping +
bağlantıda anında `: connected`. v2 landmark'lar: BOT_CREATED/
STARTED/PAUSED/RESUMED/STOPPED/ARCHIVED/STATUS, DEAL_OPENED/
CLOSED/CANCELLED/FUNDS_ADDED, SAFETY_ORDER_FILLED; runner deal +
değişimde status. UI: EventSource + tür→sorgu geçersiz kılma;
health yoklaması canlıyken durur; bağlantı noktası akışa duyarlı.
- Fiyat tick YOK (DEFERRED): fan-out/backpressure tasarımı
  gerekir; depth/ticker polling sürer.
- Bulgu: Next başlıkları ilk gövde baytına kadar tutar (8 sn
  kanıt) → anında yorum baytı; geçiş Route Handler'dan.
- Test: settings seçici kapsamlandı (olay tablosu girişimi);
  bot kurma 502/503'te BİR kez yinelenir (market-ready kuralı).
Kanıt (LOCAL): checker 2259/2259 · vitest 213/213 · tsc+lint
  temiz · e2e 68/68 · canlı: itme + replay + fixture.

## W-B8 — kalıcı olay kaydı (2026-09-26, Muse)
`EventLog(path=...)`: deque okuma modeli, SQLite (WAL) restart
günlüğü; kapasite budaması diskte de uygulanır. Yazma hatası
RAM'e düşer (uyarıyla, arayanı bozmaz); bozuk yol açılışta
hızlı hata verir. Kablolama: `DATA_DIR/events.sqlite3` (e2e
yalıtımı otomatik). v1 paper oturumları DEFERRED (tüketici yok,
v2 Paper botlar kalıcı ürün yolu).
- Test: market satırı tek çevrim sabrı (20 sn, bozuk yük kuralı).
Kanıt (LOCAL): checker 2264/2264 · e2e 68/68 · canlı: öldür+
  restart sonrası seq=1 replay, yeni kayıt seq=2.

## N1 — bildirim merkezi (2026-09-26, Muse)
Rosetli çan + açılır son olaylar + `/notifications` merkezi;
`last_seen_seq` monoton (SQLite + RAM yedeği), okundu işaretleme.
10 ekran görüntüsünde çan maskelendi (rozet koşuya göre değişir).
Kanıt (LOCAL): checker 2276/2276 · vitest 223/223 · e2e 69/69.
Sıradaki: G2 spot grid.
