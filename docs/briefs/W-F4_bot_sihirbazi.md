# muse — Görev W-F4 + W-F5a: Bot oluşturma sihirbazı + Botlar listesi/detayı

Plan: `docs/PLAN_WEB.md` §6.2, §6.3 (terminoloji §4). İşbölümü aynı: yalnız bu görev, bana rapor. `STATE.md`, `TASK.md`, `docs/KARARLAR.md`, `src/` ve `web/src/lib/decimal.ts` değiştirilmez.

## W-F8 geri bildirimi
W-F8 kabul edildi. e2e 27/27'yi kendim çalıştırdım; kill switch test sonrası kapalı kaldı. Tek düzeltme: **Canary kartındaki "Eşikler sektör varsayılanlarıdır, bu kurulum için kalibre edilmedi." notu yanlış.** Bu not rejim kartından kopyalanmış; canary'de eşik yok. Yerine şunu yaz: "Canary değerleri (tutar sınırı, günlük kayıp, pencere) henüz belirlenmedi."

## Backend sözleşmesi (hazır, tipli — `npm run gen:api` ile `schema.d.ts`'e gelir)
| Uç | Kullanım |
|---|---|
| `POST /api/v2/bots/preview` `{budget, strategy}` | Canlı plan: `reference_price`, `base_order{price,qty,amount}`, `safety_orders[{index,price,qty,amount,deviation_percent}]`, `required_funds`, `within_budget`, `price_coverage_percent`, `average_price_all_filled`, `take_profit_price`, `stop_loss_price_initial` |
| `POST /api/v2/bots` `{name, mode, budget, strategy}` | 201 → `data: Bot` (STOPPED, revision 1) |
| `GET /api/v2/bots` · `GET /api/v2/bots/{id}` | Liste / detay |
| `POST /api/v2/bots/{id}/{start\|pause\|resume\|stop\|archive}` `{revision}` | Durum işlemleri |
| `GET /api/public/symbol-rules?symbol=` | `min_notional`, `bot_supported` |
| `GET /api/public/klines` | Önizleme grafiği |

- `strategy` alanları: `symbol`, `base_order`, `safety_order` (USDT), `max_safety_orders` (0-50), `max_active_safety_orders` (null veya 1..max), `price_deviation`, `safety_order_volume_scale`, `safety_order_step_scale`, `take_profit`, `stop_loss` (%; null = kapalı). Sayılar ondalık metin olarak gönderilir.
- **Hatalar:** 422 Problem Details `errors[{field, code}]`. `field` şu biçimlerden biridir: `strategy.base_order`, `budget`, `strategy` (genel). Hata ilgili form alanının altında `detail` metniyle gösterilir.
  - Kodlar: `SECTOR_BASE_ORDER_TOO_SMALL`, `SECTOR_BUDGET_TOO_LOW`, `SECTOR_QUOTE_UNSUPPORTED`, `SECTOR_CONFIG_INVALID`, `SECTOR_FIELD_OUT_OF_RANGE`.
- **start/resume şu an `409 BOT_RUNNER_UNAVAILABLE` döner.** Otomatik çalıştırıcı (W-B2) henüz yok. Bu bir hata değil, dürüst bir durum; arayüz bunu açıkça söyler (aşağıda).

Her uç için önce gerçek yanıtı kaydet (başarılı + her hata kodu için en az bir örnek), zod şemasını ondan yaz.

## A. `/bots/new` — DCA bot sihirbazı
**Düzen:** solda adımlar, sağda yapışkan (sticky) önizleme paneli. Mobilde önizleme adımların altına iner.

**Adımlar:**
1. **Parite ve mod**
   - Parite seçici: Ctrl+K araması yeniden kullanılır; `?symbol=` ile ön dolu gelebilir.
   - `symbol-rules` ile desteklenmiyorsa seçim engellenir ve neden gösterilir.
   - Mod: **Paper** (varsayılan). **Testnet** devre dışı, ipucu: "Testnet'te otomatik çalışma için onay bekleniyor."
2. **Hazır ayar:** Muhafazakar / Dengeli / Agresif / Özel. Değerler aşağıdaki tabloda. Bir alan elle değişince seçim "Özel"e geçer.
3. **Giriş:** Base order (USDT). Alanın altında borsa minimumu gösterilir ("En az 5 USDT", `symbol-rules.min_notional`).
4. **Safety orders:** Safety order (USDT), Max safety orders, Max active safety orders (boş = sınırsız), Price deviation (%), Safety order volume scale, Safety order step scale. Her alana kısa Türkçe açıklama ipucu.
5. **Çıkış:** Take profit (%); Stop loss aç/kapa + (%).
6. **Bütçe ve isim:**
   - Bütçe = "Max amount for bot usage" (USDT).
   - "Gereken tutarı kullan" düğmesi önizlemedeki `required_funds` metnini **olduğu gibi** bütçe alanına kopyalar (istemci yuvarlama/aritmetik yapmaz).
   - İsim varsayılanı: `<SYMBOL> DCA`.
7. **Özet ve oluştur**

**Önizleme paneli:**
- Form değişince 400 ms gecikmeyle `preview` çağrılır; en son isteğin cevabı gösterilir, eskileri iptal edilir.
- **Kartlar:** Gereken sermaye (bütçeyle birlikte; `within_budget:false` ise amber uyarı), Fiyat kapsamı %, Tüm SO dolunca ortalama, TP fiyatı, Başlangıç SL fiyatı.
- **Emir tablosu:** Base order + SO1..n. Her satırda fiyat, miktar, tutar (USDT) ve sapma %.
- **Canlı mum grafiği** (1h, 150 mum) üzerinde yatay çizgiler: base order (mavi, `--entry`), her SO (amber kesik, `--safety`), tüm SO dolunca ortalama (mavi noktalı), TP (yeşil, `--profit`), SL (kırmızı, `--loss`). Çizgi değerleri **yalnız önizleme yanıtından** gelir; istemci seviye hesaplamaz.

**Oluştur:**
- "Paper botu oluştur" → `POST /api/v2/bots` → başarıda `/bots/<id>`.
- 422 hataları ilgili adıma dönüp alan altında gösterilir.

**Hazır ayar değerleri** (Claude kararı; hepsi LONG, spot):
| | Base order | Safety order | Max SO | Max active SO | Price deviation | Volume scale | Step scale | Take profit | Stop loss |
|---|---|---|---|---|---|---|---|---|---|
| Muhafazakar | 20 | 20 | 8 | 3 | 2 | 1.2 | 1.3 | 1.5 | kapalı |
| Dengeli | 25 | 25 | 6 | 2 | 1.5 | 1.5 | 1.2 | 2 | kapalı |
| Agresif | 50 | 50 | 5 | 2 | 1 | 2 | 1 | 3 | kapalı |

"Önce backtest et" düğmesi bu dilimde **yok**. Backtest ucu hazır olunca (W-F3) eklenecek; yer tutucu düğme koyma.

## B. `/bots` — liste (W-F5a)
- `GET /api/v2/bots`.
- **Masaüstü tablo:** isim, parite, durum rozeti, mod rozeti, bütçe, oluşturulma zamanı.
- **Mobil:** kart görünümü.
- **Filtreler:** durum (Tümü / Çalışıyor / Duraklatıldı / Durdu / Hata), arşivlenmişleri göster.
- **Satır eylemleri:** durum makinesine göre yalnız geçerli olanlar.
  - Çalışıyor → Duraklat, Durdur
  - Duraklatıldı → Devam, Durdur
  - Durdu → Başlat, Arşivle
  - Hata → Durdur
- **Eylem gönderimi:** her eylem güncel `revision` ile gönderilir. `409 BOT_REVISION_CONFLICT` → listeyi yenile + "Bot başka yerde değişti, liste yenilendi."
- **Başlat → `409 BOT_RUNNER_UNAVAILABLE`:** bilgi diyaloğu açılır: "Bot kaydedildi. Botları otomatik çalıştıran servis henüz devrede değil; devreye girdiğinde buradan başlatabileceksin." Hata kırmızısı kullanılmaz.
- **Boş durum:** "İlk botunu kur" → `/bots/new`.

## C. `/bots/[id]` — detay (W-F5a)
- **Başlık:** isim, parite, durum ve mod rozetleri, eylem düğmeleri (liste ile aynı kurallar).
- **"Strateji" kartı:** kayıtlı parametreler sektör etiketleriyle.
- **"Güncel plan" kartı:** kayıtlı `strategy` ve `budget` ile `preview` çağrılır; aynı tablo ve grafik çizgileri. Not: "Plan güncel fiyatla yeniden hesaplandı; deal başladığında o anki fiyat esas alınır."
- **"İstatistikler" ve "Deal'ler":** EmptyState, "Bot çalışmaya başladığında burada görünecek." Sahte veri yok.

## Sınırlar
- İstemcide finansal hesap yok. Seviye, gereken sermaye, ortalama, TP ve SL yalnız backend yanıtından gelir.
- Form sayıları metin olarak tutulur. Doğrulama backend'e bırakılır; istemci yalnız biçim (sayı deseni) ve zorunluluk kontrolü yapar.
- `Number()` yalnız `src/lib/chart/**`.
- Backend'e dokunma.
- e2e'de oluşturulan botlar test sonunda **arşivlenir** (kalıcı SQLite; birikmesin).

## Testler
- **Vitest:**
  - Hazır ayar → form değerleri.
  - Elle değişince "Özel".
  - Problem Details `field` → form alanı eşlemesi (gerçek kayıtlarla).
  - Durum → izinli eylemler tablosu (tüm durumlar).
  - "Gereken tutarı kullan" metni aynen kopyalar.
- **Playwright** (canlı backend):
  - Sihirbaz BTCUSDT Dengeli → önizleme kartları + grafik çizgileri → oluştur → detay sayfası.
  - Base order 3 → alan altında borsa minimumu hatası.
  - USDC paritesi seçilemez.
  - Listede Başlat → runner bilgi diyaloğu.
  - Arşivle → listeden kalkar.
  - axe kritik ihlal 0.
  - Görsel taban: sihirbaz masaüstü + mobil, liste, detay.

## Rapor
Her zamanki biçimde: `git status` aynen, komut son satırları, ekran görüntüleri ve yolları, sapmalar. Ek olarak: e2e sonunda arşivlenmemiş test botu kalmadığını gösteren `GET /api/v2/bots` çıktısı.
