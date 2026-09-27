# Faz G1 (SHORT runner) — SONUÇ (2026-09-26, Muse)

Kapsam: sector DCA yolunda LONG/SHORT yön desteği; motor → simülasyon →
runner → stats → API → UI uçtan uca. Futures kaldıraç/cooldown bu
dilimde yok (G1-kalan).

Backend:
- `direction` LONG/SHORT: sector parse + deal türetme + Config +
  historical simülasyon + runner + stats + v2 API (create/get/preview/
  backtest). Eski kayıtsız strateji LONG sayılır (tek-sürüm göç).
- Kısa geometri aynadır: TP girişin altında, SO kademeleri üstte;
  stop-loss yönlü. Tüm para hesabı exact Fraction, UI'da hesap yok.

Arayüz:
- Sihirbaz + backtest: Yön seçici (varsayılan Long); özet satırı ve
  URL köprüsü yönü taşır (bozuk değer atlanır).
- Deal tablosu: yön rozeti bot stratejisinden (Long/Short).

Kanıt (LOCAL):
- checker 2177/2177 PASS (1 skip) · vitest 175/175 · tsc+lint+build
  temiz · e2e 65/65 (2 backtest görseli amaçlanan değişimle yenilendi).
- Canlı: SHORT bot `bot_cfed1402cfdd` açıldı, kalıcılık okundu;
  preview TP=82667.83 SO1=85620.26 (ayna geometri doğrulandı).

Sınırlar: mainnet NO-GO; testnet mutation kapalı; review=NOT_RUN.

## G1-kalan/a — giriş kapıları (2026-09-26, Muse)
Kapsam: cooldown (sn, kapanıştan sonra bekleme) + min/max deal-açma
fiyatı; `step_closed_bar` tek kuralı (backtest ≡ paper). Referans:
bar açılışı (dolum referansıyla aynı). Cooldown restart'ta kaybolmaz
(runner her turda son kapanıştan tohumlar).
- Config/sector/API/UI + runner tohumlama; 3 kuşak eski kayıt okunur.
- max-active-deals YOK (DEFERRED): tek sembol + tek-deal motoru =
  yapısal 1; çoklu-deal motor işidir.
- Kanıt: checker 2204/2204 · vitest 182/182 · e2e 65/65 (1 geçici
  backend kopması izole koşuda yeşil) · canlı: kapı echo + bant-dışı
  backtest 0 deal.
Sıradaki: G1-kalan/b (futures DCA paper, isolated 1–10x).

## G1-kalan/b — futures DCA paper (2026-09-26, Muse)
Kapsam: market SPOT/FUTURES + kaldıraç (spot=1, futures 1–10,
default 3x); isolated (cross sonra). Gereken fon marjindir
(notional/kaldıraç, para kuantumuna YUKARI); notional tavan
bütçe×kaldıraç. Spot ekonomi bayt-bayt aynı. Likidasyon/funding
yok (G3); -%99 halt backstop'tur.
- Sector/API/UI + bot detay tam strateji kartı; create kaldıraç
  default'unu çözer (kayıt hep açık); eski kayıtlar okunur.
- Kanıt: checker 2219/2219 · vitest 185/185 · e2e 65/65 · canlı:
  FUTURES 3x echo + marj önizleme (180.93/541.18) + RUNNING.
Faz G1 KAPANDI. Sıradaki: W-B5 portföy serisi.
