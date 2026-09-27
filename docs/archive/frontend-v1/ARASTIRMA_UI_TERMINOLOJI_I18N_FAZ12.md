# Araştırma — Sektör Terminolojisi, i18n Mimarisi, Ölü Kod Envanteri ve Faz 12 Ayrıntılı Plan

**Tarih:** 2026-09-21 · Bu belge üç isteği birleştirir: (1) tüm kod tabanında hiçbir çalışan uca (API/CLI) bağlı olmayan modüllerin **tek seferlik, tam** envanteri, (2) 3Commas/Pionex/Bitsgap referans ekranlarının DCABOT'un mevcut terminolojisiyle karşılaştırılması + i18n mimarisi, (3) bunların hepsini kapsayan ayrıntılı Faz 12 uygulama planı.

---

## 1. Ölü/bağlanmamış kod — tam envanter (import-graph reachability, tek seferlik)

**Yöntem:** `src/dcabot/` altındaki 158 modülün her biri için, `src/dcabot/server/api.py` ve `tools/*.py`'den (tüm CLI script'leri) başlayarak **geçişli import grafiği** çıkarıldı (grep değil — gerçek `from dcabot.X import Y` / `import dcabot.X` ayrıştırması). Sonuç: **70 modül hiçbir çalışan API endpoint'inden veya CLI aracından — doğrudan ya da dolaylı — asla import edilmiyor.** Bunlar test dosyalarında (`tests/`) referans edilmiş olabilir (yani ünite testleri geçiyor) ama **canlı sunucu hiçbirini hiçbir zaman çağırmıyor.**

Bu, önceki oturumda tek tek bulduğum (`signal_intake.py`'nin HMAC/replay fonksiyonları) durumun genel halidir — o bir istisna değil, bu kod tabanının sistemik bir deseniydi: her araştırma dilimi kendi sözleşme/contract dosyasını "tamamlanmış" olarak kapatıyor ama onu gerçek bir HTTP/CLI ucuna bağlamak ayrı, genelde hiç yapılmamış bir adım kalıyor.

### Küme A — Futures DCA ürünü (24 dosya, en büyük ve en değerli küme)
`application/futures_dca_{candidate_acceptance,core_mapping,core_replay_oracle,event_contract,exit_candidate,exit_identity,exit_priority,fee_aware_exit,migration_preflight,profile_source,recovery_capability,recovery_provenance_gate,recovery_snapshot,reservation,start_gate,stop_contract,take_profit}.py` + `persistence/futures_dca_{core_binding,core_replay_store,event_store,journal_schema,provenance_target,release_store,release_transition}.py`.

Bu, **Pionex'in ekran görüntüsünde gösterdiğin "Futures DCA Bot" ürünüyle bire bir aynı kavram** — anchor/safety/exit/recovery/replay hepsi ayrı ayrı sözleşme dosyalarında var, `docs/OZELLIK_MATRISI.md`'de `P1.12.g.*`/`P1.12.h.*` claim ID'leriyle belgeli (bilinçli, "contract-ready/implementation-pending" statüsünde bırakılmış — dokümantasyon eksikliği değil, bilinçli duraklama). **Faz 5'in futures mutation katmanı PLAN kararı bu kümeyi kapsıyor.** Değer: neredeyse hazır bir "Futures DCA Bot" — Pionex ekranındaki özelliğin DCABOT'ta zaten %80 kodu var, sadece hiçbir yere bağlı değil.

### Küme B — Futures Grid gerçek yürütme (9 dosya)
`application/futures_grid_{advanced_gate,local_lifecycle,local_policy,margin,order_placement,pnl,position,replacement_replay_gate,variant_gate}.py`.

Önceki turda "Grid Bot'ta sadece hesap motoru var, gerçek bot yok" demiştim — **bu yanlıştı**: gerçek grid **yürütme** (order placement, position tracking, margin, lifecycle) kodu zaten var, sadece `api.py`'nin gördüğü tek şey basit `futures_grid_levels.py` (seviye hesaplayıcı). Bu küme bağlanırsa 3Commas/Bitsgap'teki "Grid Bot" ekranının arkasındaki gerçek motor ortaya çıkar.

### Küme C — Canlı güvenlik kapıları (2 dosya, **öncelik: kritik, ayrı ele alınmalı**)
`application/canary_policy.py`, `application/live_gate.py`.

STATE.md/AGENTS.md bunları "altyapı tamam, kapı kilitli" diye tanımlıyor — bu okura "canlı bir koruma mekanizması var, sadece onay bekliyor" izlenimi veriyor. **Gerçek durum: hiçbir çalışan kod yolu bu iki dosyayı hiç çağırmıyor.** Bugün mainnet emri gönderen bir kod yolu zaten yok, dolayısıyla pratik risk sıfır — ama gelecekte biri yanlışlıkla yeni bir mutation kod yolu eklerse, bu "kapı" fiilen orada değil, sadece testlerde var. **Öneri: STATE.md/AGENTS.md'deki "kilitli canlı kapı" ifadesi "kilit mekanizması kodlandı ama hiçbir kod yolundan çağrılmıyor (test-only)" diye netleştirilmeli** — bu bir kod değişikliği değil, dürüstlük/dokümantasyon düzeltmesi.

### Küme D — Gerçek venue hesap/rezervasyon/mutabakat katmanı (~26 dosya)
`application/account_reservation.py`, `account_reservation_ledger.py`, `balance_percent_sizing.py`, `conditional_execution.py`, `isolated_liquidation.py`, `ladder_binding.py`, `lifecycle_policy.py`, `market_base_quantity.py`, `market_execution_reconciliation.py`, `order_list_reconciliation.py`, `order_sender.py`, `pause_order_policy.py`, `reinvestment_budget.py`, `shared_account_identity.py`, `sizing_pre_acceptance.py`, `sizing_units.py`, `spot_grid_cycle_accounting.py`, `spot_inventory_projection.py`, `spot_lifecycle_core_binding.py`, `spot_order_lifecycle.py`, `venue_event_binding.py`, `venue_spot_event_mapping.py` + `persistence/{conditional_execution_store,linear_ledger_store,market_execution_store,order_list_event_store,order_list_store,reconciliation_journal,spot_binding_store}.py`.

Bu, gerçek Binance mutabakatı/rezervasyon/paylaşımlı-hesap için araştırma-ağır bir katman — Faz 3/5/9'un zaten bilinen `LOCAL_CODE_REQUIRED`/`DEFERRED`/`BLOCKED` maddeleriyle örtüşüyor (F31 shared-account, LCR-12 liquidation, vb.). Yeni bir sürpriz değil, ama tek yerde toplanmış hali ilk kez burada var.

### Küme E — Overfitting/backtest kimlik altyapısı (2 dosya)
`application/chronological_split.py`, `application/horizon_overlap.py` — Faz 14 araştırmasında (`docs/ARASTIRMA_ILERI_BACKTEST_SINYAL_KALITE.md`) zaten ele alındı; CPCV'nin temel taşları ama hiçbir yere bağlı değil.

### Küme F — Diğer (7 dosya)
`dcabot.bootstrap`, `dcabot.domain.math`, `dcabot.persistence.store` — bunlar **en eski** (muhtemelen P1'in ilk haftalarından kalma) dosyalar; `tools/bot.py` (README'nin hâlâ "P1.01 local arayüzü" diye andığı, güncelliğini yitirmiş CLI demo) bile artık bunları kullanmıyor, ham `sqlite3` ile kendi başına çalışıyor. **Bu üçü muhtemelen gerçek ölü kod (kullanılmayan ilk-nesil prototip)** — küme A-D gibi "bilinçli bekletilmiş" değil, düzenli temizlik adayı.

### Sonuç ve öneri
70 dosyanın ~62'si (küme A/B/D/E) **bilinçli, belgeli, bekletilmiş araştırma/sözleşme kodu** — "ölü kod" değil, "henüz kablosu çekilmemiş" kod. Küme C (2 dosya) **dokümantasyon-gerçeklik uyumsuzluğu**, düzeltilmeli. Küme F (3 dosya, `bootstrap`/`domain.math`/`persistence.store`) muhtemelen gerçek temizlik adayı — ayrı, küçük bir dilimde doğrulanıp silinebilir veya arşivlenebilir.

**Bundan sonra bu liste tekrar "keşfedilmeyecek":** her yeni fazda `tools/phase_gate.py`'ye bu reachability taramasını ekleyip (dosya var mı + test var mı kontrolüne ek olarak "api.py veya tools/ tarafından import ediliyor mu" kontrolü) drift'i otomatik yakalamak öneriliyor — bu, ileri bir dilimde eklenebilecek küçük bir araç değişikliği.

---

## 2. Terminoloji karşılaştırması — sektör standardı vs DCABOT

Referans ekranlarından (3Commas DCA/Grid/Signal Bot, Pionex Futures DCA, Bitsgap DCA/Grid) çıkarılan **evrensel** terimler (üç üründe de aynı/çok yakın) ile DCABOT'un mevcut arayüz metni karşılaştırıldı:

| Kavram | Sektör terimi (EN) | DCABOT şu an | Önerilen (TR, sektöre yakın) |
|---|---|---|---|
| İlk emir | Base order | "Anchor fiyatı" (yalnız fiyat, emri değil) | **Baz Emir** (miktar+fiyat birlikte) |
| DCA ek alım kademesi | Safety order / Averaging order | "Safety miktarı" | **Güvenlik Emri** (aynen korunuyor, zaten yakın) |
| Maks. ek alım sayısı | Max safety orders / Averaging orders quantity | "Safety sayısı" | **Güvenlik Emri Sayısı** |
| Fiyat sapma eşiği | Price deviation % | "Sapma" | **Fiyat Sapması %** |
| Miktar/hacim çarpanı | Volume multiplier | `volume_multiplier` (yalnız ham sayı, etiketsiz) | **Hacim Çarpanı** |
| Adım çarpanı | Step multiplier | `step_multiplier` (etiketsiz) | **Adım Çarpanı** |
| Kâr al | Take Profit (TP) | `take_profit` (motor alanı, UI'da ayrı etiketli alan yok) | **Kâr Al (TP)** — bağımsız UI alanı olmalı |
| Zarar durdur | Stop Loss (SL) | Yok | **Zararı Durdur (SL)** — yeni alan |
| İz süren zarar durdur | Trailing Stop | `ExitPanel`'de var ama ayrı "lab" aracı, bot kurulumunda değil | **İz Süren Zararı Durdur** — bot kurulumuna taşınmalı |
| Bot başlatma koşulu | Bot start condition: Immediate / Indicator / Webhook alert | Yok (bot her zaman "immediate" gibi davranıyor) | **Bot Başlatma Koşulu**: Hemen / İndikatör / Webhook |
| Grid tipi | Grid type: Long / Neutral / Short / Hedge | Yok (yalnız serbest metin "Yön") | **Grid Tipi**: Uzun / Nötr / Kısa / Hedge |
| Grid boyutu | Grid size: Interval / Infinite | Yok | **Grid Boyutu**: Aralıklı / Sonsuz |
| Grid başına kâr | Profit per Grid % | Yok | **Grid Başına Kâr %** |
| Hızlı kurulum | Quick Setup: Short/Mid/Long-term | Yok (Template import var ama farklı akış) | **Hızlı Kurulum**: Kısa/Orta/Uzun Vadeli |
| Manuel ayarlar (katlanır) | Manual adjustment | Kısmen (form zaten düz, disclosure var) | **Manuel Ayarlar** |
| Yatırım tutarı | Investment / Amount per trade | "Bütçe" (yalnız sihirbazda, strateji formunda yok) | **Yatırım Tutarı** |
| Al-Sat/Pump-Dump koruması | Pump/Dump Protection | Yok | **Ani Hareket Koruması** |
| Kâr yeniden yatırımı | Reinvest profit | Yok | **Kârı Yeniden Yatır** |
| Toplam hedef kâr/zarar | Target total profit / Allowed total loss | Yok | **Hedef Toplam Kâr / İzin Verilen Toplam Zarar** |
| Geriye dönük test | Backtest (formun içinde, tek tık) | "Historical Runs" (tamamen ayrı üst-seviye akış) | **Geriye Dönük Test** düğmesi, forma gömülü |

**En kritik yapısal terminoloji sorunu terim değil, akış:** DCABOT'ta "bot" iki ayrı, birbirine bağlı olmayan kavram olarak var — `BotWizard.tsx`'in 5 adımı (Kimlik/Pariteler/Listeler/Bütçe/Önizleme) yalnız **bot kaydı/sahiplik** soruyor; asıl DCA parametreleri (baz emir, güvenlik emri, sapma, TP/SL) tamamen ayrı bir panelde ("Bot stüdyosu"). Sektör ürünlerinde bunlar **tek, kesintisiz bir "Create Bot" akışı**. Bu, terminoloji tablosundan daha önemli bir Faz 12 maddesi (bkz. §4.2).

---

## 3. i18n Mimarisi — Tek XML, EN/TR + kolay genişleme

İstenen: (a) EN/TR dil seçimi, (b) yeni dil eklemek yalnız **tek bir XML dosyasına** çeviri eklemek olsun, (c) kod tarafında bir çakışma çıkarsa **iç kod adları değişmesin, yalnız görünen isim (takma ad) değişsin**.

### 3.1 Dosya formatı
Tek dosya: `frontend/src/locales/strings.xml`. Her UI metni bir `<string>` elemanı, `key` kod tarafından hiç değişmeyen kararlı bir tanımlayıcı (backend/domain alan adlarıyla **karışmayan**, salt UI-katmanı bir ad alanı — örn. `dca.baseOrder.label`, asla `anchor_price` gibi bir Python/TS alan adını birebir kopyalamaz):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<resources>
  <string key="dca.baseOrder.label">
    <tr>Baz Emir</tr>
    <en>Base Order</en>
  </string>
  <string key="dca.safetyOrder.label">
    <tr>Güvenlik Emri</tr>
    <en>Safety Order</en>
  </string>
  <string key="dca.deviation.label">
    <tr>Fiyat Sapması</tr>
    <en>Price Deviation</en>
  </string>
  <string key="exit.takeProfit.label">
    <tr>Kâr Al</tr>
    <en>Take Profit</en>
  </string>
  <!-- ... -->
</resources>
```

Yeni bir dil eklemek = her `<string>` bloğuna bir `<de>`/`<fr>` çocuğu eklemek — hiçbir kod değişikliği gerekmez.

### 3.2 Yükleme mekanizması (frontend, ek kütüphane gerektirmez)
Tarayıcının yerleşik `DOMParser`'ı ile derleme zamanında (Vite plugin) ya da ilk yüklemede XML, `{key: {tr, en}}` şeklinde düz bir JS nesnesine dönüştürülür ve React Context üzerinden `t("dca.baseOrder.label")` fonksiyonuyla tüketilir. Vite plugin tercih edilir (derleme zamanı dönüşüm → çalışma zamanı XML parse maliyeti sıfır, tip-güvenli anahtar listesi otomatik üretilebilir).

### 3.3 "Kod tarafında aksaklık" güvencesi
Kural: **XML `key` alanları hiçbir zaman** Pydantic model alanı, TS tip alanı, veya domain/application modül adıyla bire bir aynı olmayacak — her zaman `<bölüm>.<alan>.<rol>` (`label`/`helper`/`error`) deseninde, UI'a özel bir ad alanında yaşayacak. Böylece backend bir alanı yeniden adlandırsa bile (nadiren, ve zaten yalnız Claude'un dokunabildiği kritik dosyalarda) UI metni etkilenmez — **takma ad prensibi baştan mimariye gömülü**, sonradan yama değil.

### 3.4 Dil seçici
`AppShell`'deki mevcut tema-değiştirme düğmesinin (☾/☀) yanına bir "TR/EN" düğmesi; seçim `localStorage`'da saklanır (per-viewer, sunucuya gitmez — proje "UI hesap yapmaz" ilkesiyle tutarlı, salt görüntü tercihi).

---

## 4. Faz 12 — Ayrıntılı uygulama planı

Kapsam: hem **görünüm** (3Commas/Pionex/Bitsgap'e görsel/akış paritesi) hem **işlev** (DCABOT'un zaten sahip olduğu — ve §1'de ortaya çıkan bağlanmamış — motor gücünün gerçek arayüze taşınması). AGENTS.md'nin "aynı alt sistemde art arda en fazla 3 dilim" kuralına göre alt-dilimlere bölündü; her dilim kendi başına kullanıcı-görünür bir sonuç üretir.

### 12.1 — Chart altyapısı (temel, diğer her şey buna bağlı)
- Kütüphane: hafif, bağımlılığı az bir mum-grafik kütüphanesi (ör. `lightweight-charts` — TradingView'ın kendi açık kaynak kütüphanesi, MIT lisanslı, React sarmalayıcısı kolay yazılır) — **Pine Script çalıştırmaz, yalnız görsel render**, DCABOT'un "no float in financial calc" kuralını ihlal etmez çünkü yalnız zaten-hesaplanmış Decimal-string OHLC'yi piksel koordinatına çeviren bir render katmanıdır (tıpkı mevcut `HistoricalChart.tsx`'in SVG path'i gibi, sadece mum+hacim+indikatör çizebilen).
- `historical-runs/{id}/chart-data` zaten var — yalnız tüketici değişir (SVG path yerine candlestick chart).
- Backtest (Historical Runs) VE canlı/paper (mevcut `PaperPanel` print akışı) aynı chart bileşenini paylaşır — iki ayrı grafik yazılmaz.
- Kabul ölçütü: bir dataset seçilince gerçek mum+hacim grafiği render olur; paper trading'te canlı print'ler grafiğe akar.

### 12.2 — Birleşik "Bot Oluştur" akışı (BotWizard + Bot stüdyosu birleşimi)
- `BotWizard`'ın 5 adımı (Kimlik/Pariteler/Listeler/Bütçe/Önizleme) ile "Bot stüdyosu"nun parametreleri (§2 terminoloji tablosu) **tek sihirbazda** birleştirilir: 1) Kimlik+Parite → 2) Baz+Güvenlik Emri (Entry) → 3) Kâr Al/Zarar Durdur/İz Süren (Exit) → 4) Bütçe/Yatırım → 5) sağda canlı chart+önizleme (§12.1'e bağımlı) → Backtest düğmesi → Kaydet.
- Terminoloji tablosundaki tüm etiketler i18n XML üzerinden (§3) — kod tarafında yalnız yeni `<string>` anahtarları eklenir, hiçbir Pydantic/TS alan adı değişmez.
- "Botlar & Stratejiler" sekmesindeki 16 aracın geri kalanı (Templates/Signal/Futures/TwoLeg/Rebalance/Risk) sihirbazın **dışında**, ayrı bir "Gelişmiş Araçlar" alt-navigasyonuna taşınır (varsayılan kapalı) — 3Commas/Pionex'in de "Bots" ana ekranının sade, araştırma araçlarının ayrı sekmelerde olduğu deseniyle örtüşür.

### 12.3 — Grid Bot gerçek akışı (Küme B'yi bağlama)
- §1 Küme B'deki gerçek grid yürütme motoru (`futures_grid_order_placement`/`position`/`margin`/`local_lifecycle`) `api.py`'ye bağlanır; UI'da Grid Tipi (Long/Neutral/Short/Hedge) + Grid Boyutu (Aralıklı/Sonsuz) + Grid Başına Kâr % alanları eklenir (§2 terminoloji).
- Mutation gate disiplini korunur — bu dilim yalnız testnet'te, mevcut mutation-onay akışıyla aynı yazılı-onay kuralına tabi.

### 12.4 — Sinyal/Webhook bot görünümü + terminoloji (Faz 13 ile birleşir)
- `SignalPanel` yeniden tasarlanır: "Bot start condition: TradingView Indicator" tarzı 3-adımlı akış (Ayarlar→Alertler→Başlat), Faz 13'ün gerçek webhook endpoint'ine bağlı.

### 12.5 — i18n altyapısı + terminoloji geçişi (§3)
- `strings.xml` + Vite plugin + `t()` fonksiyonu + TR/EN düğmesi.
- Tüm mevcut sabit-Türkçe metinler (App.tsx + 19 panel dosyası) kademeli olarak `t()` çağrılarına taşınır — büyük ama mekanik bir refactor, App.tsx'in useState→useReducerGroup geçişiyle aynı risklilikte (davranış değişmez, yalnız metin kaynağı değişir).

### 12.6 — Küme C/F temizliği (küçük, bağımsız dilim)
- `canary_policy.py`/`live_gate.py` için STATE.md/AGENTS.md ifadesi netleştirilir (kod değişikliği değil, dürüstlük düzeltmesi).
- `bootstrap.py`/`domain/math.py`/`persistence/store.py`'nin gerçekten kullanılmadığı doğrulanıp (tools/bot.py dahil hiçbir yerde) arşive taşınır veya silinir.

**Sıra önerisi:** 12.1 (chart) → 12.5 (i18n altyapısı, erken kurulmalı ki 12.2 baştan `t()` ile yazılsın) → 12.2 (birleşik akış) → 12.3 (grid) → 12.4 (sinyal, Faz 13 ile paralel) → 12.6 (temizlik, herhangi bir zamanda bağımsız).

---

## Kaynaklar
- Bu bölümdeki terminoloji karşılaştırması doğrudan kullanıcının paylaştığı ekran görüntülerinden (3Commas Create DCA/Grid/Signal Bot, Pionex Futures DCA Bot, Bitsgap DCA/Grid/BTD/Loop/Combo) çıkarıldı.
- Ölü-kod envanteri: bu oturumda `src/dcabot/` üzerinde çalıştırılan özel bir import-graph reachability betiği (dosya değil, tek seferlik analiz).
- i18n mimarisi: genel frontend mühendislik pratiği (Android `strings.xml` deseninden esinlenilmiştir), DCABOT'a özel yeni tasarım — dış kaynak gerektirmedi.
