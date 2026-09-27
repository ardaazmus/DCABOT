# Faz AB — Yerleşim, bilgi mimarisi ve kullanım kolaylığı (qwen'e gerçek parite)

Tarih: 2026-09-24 · Karar/brief: Claude · Uygulama (UI): muse · Doğrulama: Claude
Referans: `docs/qwen_referans/iterasyonlar/` #14 (ekran içerikleri), #21/#22 (bitmiş nav + genel bakış),
#17 (Strateji Lab), `qwen-sohbet-export.json` (Arda'nın kendi istekleri: msg8/10/12/14/16).

## 1. Ölçülen fark (canlı uygulama, 2026-09-24)

| Ekran | Sayfa yüksekliği | Başlık | Buton | Girdi alanı |
|---|---|---|---|---|
| Botlar & Stratejiler | **16.043 px (~13 ekran kaydırma)** | **54** | 86 | **118** |
| Piyasa & Veri | 6.846 px | 11 | 16 | 39 |
| Olaylar & Denetim | 2.151 px | 7 | 20 | 8 |
| Genel Bakış | 1.989 px | 7 | 18 | 0 |
| Ayarlar | 1.274 px | 1 | 4 | 0 |

qwen'de her ekran **tek bir işe** ayrılmış, 1–9 panel; nav 8–13 görev-odaklı öğe (#22: Genel Bakış,
Botlarım, Aktif İşlemler, Strateji Lab, Backtest, Execution, Motor Testleri, Deploy).

## 2. Kök neden

`frontend/src/appSections.ts` — Faz 11 kararı "kalıcı 5-bölüm sol nav (M3 sınırı)". Faz 4–10 ve AA'da eklenen
her yetenek bu 5 kovadan birine üst üste yığıldı. Sonuç: bot oluşturma, deal yaşam döngüsü, trailing,
rebalance, şablon, sinyal botu, futures lab, hedge, scheduler, risk, korelasyon, rejim, modül defteri —
hepsi tek "Botlar" sayfasında, üç katlanır `<details>` içinde.

## 3. Somut kullanılabilirlik sorunları

1. **Görev ayrımı yok:** Backtest (OPT, WF/MC) "Piyasa & Veri"de; kaydedilmiş koşular "Olaylar"da; risk araçları
   Botlar'ın içinde katlanmış. Kullanıcı bir işi yapmak için 3 bölüm gezmek zorunda.
2. **Tıkla → detay akışı yok:** qwen'de (ve Arda'nın msg10/14/16 isteğinde) bot kartı → tam sayfa bot detayı
   (grafik + aktif ayarlar + o botun deal'ları, üstte diğer botlara hızlı geçiş şeridi); deal satırı → tam sayfa
   işlem detayı. Bizde "Bot seçili değil" paneli + tablo; deal detayı "Klasik Görünüm"e gömülü.
3. **Grafikler boş:** Botlar, Bot Oluştur ve Piyasa'daki grafik "Veri bekleniyor — Piyasa & Veri'den dataset
   seçin" diyor. Arda'nın msg8/12 isteği: grafik her yerde canlı (Binance public + Lightweight Charts) ve botun
   SO/TP/SL/likidasyon seviyelerini form değiştikçe göstermeli. Canlı mum ucu backend'de yok
   (yalnız ticker-24h ve depth var).
4. **İki bot-oluşturma yolu:** yeni "Bot Oluştur" + "Klasik Görünüm" içindeki eski BotWizard.
5. **Tekrarlar:** piyasa grafiği Botlar+Piyasa'da; sembol seçici Genel Bakış+Piyasa'da; strateji karşılaştırma
   Şablonlar+Lab'da; portföy Genel Bakış+Lab'da.
6. **Geliştirici jargonu kullanıcı yüzeyinde:** "Ladder planı", "Session sahipliği", "Lifecycle olayı",
   "Yük hash'i", "İki-seri kapı-değerlendirmesi", "Yerleşim değerlendirmesi", "Replay", "fixture", µs zaman
   alanları, APPROVED/PENDING, CANARY_NOGO, UNREADABLE.
7. **Test düzeneği gibi formlar:** "Fill listesi (JSON)", "Olay listesi (JSON)", "Yük (JSON)",
   "satır başına: ASSET MİKTAR" textarea'ları — bunlar mühendislik doğrulama araçları, kullanıcı özelliği değil.
8. **Elle teknik kimlik:** Bot oluştururken "Bot kimliği" zorunlu alan; session_id'ler elle.
9. **Genel Bakış düzen hatası:** "Durum & Veri Kaynağı" kartı sayfanın 1/3'üne sıkışmış, alt kartlarda metin
   harf harf kırılıyor ("BOTLAR & / DEAL'LER"), sağ taraf boş. qwen: üstte 4 KPI kutusu → grafik → akış → açık işlemler.
10. **Görsel kit uygulanmamış:** renk token'ı + font var; qwen'in `.panel` (cam), `.chip/.dschip` (hap rozet),
    `.livebadge/.simbadge`, `.switch`, stat-kutusu, `.bar`, nav aktif gradyanı, `.bg-grid`, `fadeUp` animasyonu yok.
    (Tam CSS: #14 ve #22 dosyalarının `<style>` bloğu — birebir alınabilir.)

## 4. Hedef bilgi mimarisi (5-bölüm sınırı kaldırılır — Faz 11 kararının yerine geçer)

| # | Nav öğesi | İçerik (mevcut bileşenlerden taşınır) | qwen referansı |
|---|---|---|---|
| 1 | 📊 Genel Bakış | 4 KPI kutusu (portföy/aktif bot/açık deal/bugünkü kâr) → canlı grafik + kâr grafiği → olay akışı → açık işlemler özeti (tümünü gör →). Sistem durumu üst çubukta kompakt şerit. Durum Asistanı sağ alt açılır panel. | #14 sec-overview, #22 |
| 2 | 🤖 Botlarım | Bot kartları ızgarası + filtre chip'leri (Tümü/DCA/Grid/Futures/Sinyal) + "Yeni Bot". Kart → `#bots/<id>` tam sayfa **Bot Detay**: üstte diğer botlar şeridi (2 satırdan sonra kaydırma), canlı grafik + bot seviyeleri, aktif ayarlar, bu botun deal'ları, istatistik. | #14 sec-bots/botdetail |
| 3 | ➕ Bot Kur | Tek oluşturma yolu: solda adımlı form, sağda **canlı** önizleme grafiği (SO/TP/SL/liq çizgileri form değiştikçe). Hazır ayar chip'leri (Muhafazakar/Dengeli/Agresif). Bot kimliği otomatik. "Paper'da Başlat" burada. Eski BotWizard UI'dan kaldırılır. | #14 sec-dca |
| 4 | 💼 Aktif İşlemler | Deal tablosu (sembol, yön, ort. giriş, güncel, PnL%, SO doluluk, TP mesafe). Satır → `#deals/<id>` tam sayfa **İşlem Detayı**: grafik + seviyeler + aksiyonlar + bağlı bot + zaman çizgisi. | #14 sec-deals/dealdetail |
| 5 | ⚙️ Backtest | Adım 1 veri (katalog+ön-kontrol tek seçicide) → Adım 2 profil/parametre → Çalıştır → sonuç (equity, Sharpe, işlem noktaları, işlem listesi). Alt sekmeler: Optimizasyon · Overfitting (WF/MC) · Kayıtlı Koşular (+karşılaştırma). | #14 sec-backtest |
| 6 | 🧪 Strateji Lab | Sekmeli: Karşılaştır · Şablonlar · Portföy · Rebalance · Sinyal Botu · Futures/Grid. Aynı anda tek araç görünür. | #17 |
| 7 | 🛡️ Risk | Kill-switch/Canary, "Neden işlem açılmıyor", Korelasyon, Rejim, Funding. | #14 sec-risk |
| 8 | 📈 Piyasa & Veri | Sembol detayı + venue snapshot + order book + dataset kataloğu/datastore + yerel dosya içe aktarma. | #14 sec-datastore |
| 9 | 🧰 Sistem | Olay merkezi, yedek/doğrulama, sistem sağlığı, modül kayıt defteri, testnet hesabı, ayarlar. Katlanmış "Geliştirici araçları": JSON/fixture girdili hesaplayıcılar (futures lifecycle, hedge replay, manuel sinyal fixture, rebalance textarea). | #14 sec-core/deploy |

Lab'daki "Whale Wall (yakında)" Strateji Lab'e taşınır. Sembol seçici global üst çubukta (tek örnek).

## 5. Tasarım kuralları (her dilimde bağlayıcı)

1. Bir ekran = bir görev. Birincil ekranlar ≤ ~2 ekran yüksekliği; fazlası sekmeye bölünür, `<details>` yığını yok.
2. Liste → kart/tablo; tıklama → tam sayfa detay (hash rota), geri butonu + hızlı geçiş şeridi.
3. Grafik asla boş değil: varsayılan canlı mum (yeni `/api/public/klines`); dataset yalnız Backtest'te.
4. Kullanıcı yüzeyinde jargon yok (sözlük: Ladder planı→Emir kademeleri, Session→Oturum, Lifecycle→İşlem
   geçmişi, Replay→Yeniden oynat, APPROVED/PENDING→Onaylı/Onay bekliyor, CANARY_NOGO→Canlı işlem kapalı).
   Kod-değerleri (enum) yalnız ipucu/tooltip'te. µs alanları → tarih/saat seçici (dönüşüm istemcide yalnız biçim).
5. Teknik kimlikler otomatik üretilir; kullanıcı yalnız isim girer.
6. Görsel kit: #14/#22 `<style>` bloğundaki sınıflar `styles.css`'e token'larla taşınır; nav emoji/ikon + aktif gradyan;
   KPI stat-kutusu bileşeni; hap-rozet bileşeni (canlı/paper/sim/uyarı varyantları).
7. **Değişmez finans disiplini:** istemcide finansal hesap yok; sunucu exact-metinleri aynen; grafikler BigInt
   sabit-nokta → yalnız pikselde `Number()`; dürüst-boş (null → "—") korunur. Mevcut backend uçları değişmez.

## 6. Dilimler ve sahiplik

| Dilim | İş | Sahip |
|---|---|---|
| AB.0 | `GET /api/public/klines` (anahtarsız Binance public mum, symbol/interval/limit allowlist, exact-metin) + testler | **Claude** |
| AB.1 | Görsel kit (panel/chip/rozet/switch/stat/bar/bg-grid/fadeUp) + kabuk: 9-öğe nav, üst çubuk (global sembol + durum şeridi), hash rota altyapısı (`#bots/<id>`, `#deals/<id>`) | muse |
| AB.2 | Genel Bakış yeniden düzeni (KPI → grafik → akış → açık işlemler); durum kartı düzen hatası | muse |
| AB.3 | Botlarım kart ızgarası + Bot Detay tam sayfa | muse |
| AB.4 | Bot Kur tek yol + canlı önizleme grafiği (AB.0'a bağlı); BotWizard UI'dan kaldırılır | muse |
| AB.5 | Aktif İşlemler tablo + İşlem Detayı tam sayfa | muse |
| AB.6 | Backtest ekranı (Piyasa'dan OPT/WF-MC, Olaylar'dan Kayıtlı Koşular taşınır) | muse |
| AB.7 | Strateji Lab (sekmeli) + Risk ekranı | muse |
| AB.8 | Piyasa & Veri sadeleştirme + Sistem ekranı + Geliştirici araçları alanı | muse |
| AB.9 | Jargon temizliği (tüm etiketler, `locales/strings.xml`) | muse |

Sıra: AB.0 ∥ AB.1 → AB.2 → AB.3 → AB.4 → AB.5 → AB.6 → AB.7 → AB.8 → AB.9.

## 7. Kabul (her dilim)

- muse raporu: değişen dosyalar + **qwen referansıyla yan yana ekran görüntüsü** + `npx tsc -b` + `npx vitest run`.
- Claude doğrulaması: taze dev-server'da kendi ekran görüntüsü (metin karşılaştırması kabul değildir), sayfa
  yüksekliği/başlık sayısı ölçümü, tıkla→detay akışı elle, finans disiplini diff incelemesi, testler.
- Faz AB kapanışı: 9 ekranın her biri qwen karşılığıyla görsel olarak yan yana; Botlar sayfası artık tek görev.
