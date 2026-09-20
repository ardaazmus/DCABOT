# P1.16.f — Warmup leakage ve readiness binding karar kapısı

## Karar

- Durum: `DEFERRED / NO-GO / RESEARCH_AUDITED / LOCAL_PASS`
- Kod değişikliği: yok
- Bağımsız review: `NOT_RUN`
- Production readiness: `NO`
- Sonraki tek iş: `P1.16.g` local feature/label horizon ve gerçek run binding karar kapısı

## Neden kod açılmadı?

Araştırma warmup döneminin indicator/feature state hazırlığı için kullanılabileceğini, ancak warmup döneminde trading veya emir üretilemeyeceğini kabul ediyor. Projede mevcut `signal_readiness.py` saf bir readiness sınıflandırması yapıyor ve `READY` sonucu bile candidate/order/fill üretmiyor. Ancak gerçek bir indicator/feature hesaplayıcısı, warmup örnek sayısının gerçek feature lookback’a bağlanması ve bu readiness sonucunun tarihsel ekonomik runner’a bağlanması mevcut değildir.

Bu nedenle yeni bir warmup sayısı, indikatör, sinyal authority’si veya “warmup sırasında fill oluşmaz” şeklinde end-to-end ekonomik kanıt üreten kod yazılmadı. Mevcut gate’in adı değiştirilerek binding varmış gibi gösterilmedi.

## Mevcut kanıt

- `src/dcabot/application/signal_readiness.py` yalnız `WAITING_FOR_CLOSED_BAR`, `STALE`, `WARMING_UP` ve `READY` sınıflandırır.
- `tests/test_signal_readiness.py` incomplete warmup’ın `WARMING_UP` kaldığını ve `READY` nesnesinde `orders`/`fills` alanı bulunmadığını doğrular.
- Bu, saf readiness sınırıdır; gerçek feature/indicator lookback, historical runner, fill reducer veya economic result binding kanıtı değildir.

## Araştırma-önce yeniden doğrulama

Resmî/primer teknik kaynaklar genel sözleşmeyi doğruluyor:

- QuantConnect LEAN warm-up veriyi geçmişten geçirerek indicator/algorithm state hazırlıyor ve warm-up sırasında trade yerleştirilmesine izin vermiyor: <https://www.quantconnect.com/docs/v2/writing-algorithms/historical-data/warm-up-periods>.
- Freqtrade `startup_candle_count` değerini stabil indicator hesapları için gereken en uzun history olarak kullanıyor; başlangıçtaki unstable period backtest kapsamından çıkarılıyor: <https://www.freqtrade.io/en/latest/strategy-customization/>.
- Freqtrade akışında candles → indicators → signals → orders ayrımı açıkça tanımlanıyor; signal bulunması bile her durumda order oluşacağı anlamına gelmiyor: <https://www.freqtrade.io/en/stable/strategy-101/>.

Bu kaynaklar DCABOT için sabit bir warmup sayısı seçmeye yetmez. Exact sayı; yerel feature lookback’leri, closed-bar üretimi, label future horizon’ı ve varsa settlement/observation horizon’ı üzerinden türetilmelidir. Freqtrade’in recursive/unstable-period uyarısı da yalnız indicator period’ünü kopyalamanın güvenli bir DCABOT policy’si olmadığını gösterir.

Yerel yeniden tarama sonucu:

- `src/dcabot/application/signal_readiness.py` yalnız caller tarafından verilen warmup sayısını sınıflandırıyor.
- `src/dcabot/application/historical_simulation.py` OHLCV barlarını mevcut reducer’a doğrudan bağlıyor; feature/indicator/label üretmiyor.
- `src/dcabot/application/historical.py` dataset + offline config planı kuruyor; feature/label/readiness adapterı bağlamıyor.
- `src/dcabot/application/historical_run_contract.py` snapshot ve identity kanıtı üretiyor; feature/label horizon authority’si taşımıyor.

Bağımsız stdlib oracle şu sınırları PASS verdi: birden fazla lookback için gereken warmup `max(lookback)` olarak türetilir; feature zamanının future label bitişinden önce olması gerekir; readiness false iken action listesi boş kalır. Bu oracle genel matematik sınırını doğrular, DCABOT’ta eksik olan pipeline’ı üretmez.

## Kontroller

- `tests.test_signal_readiness` → `6/6 PASS`.
- Bağımsız stdlib warmup/lookahead oracle → `PASS`.
- Bundled Python `3.12.14` ile `python -m compileall -q src tests` → `PASS`.
- `tools/run_checks.py` ve `tools/check_workspace.py` → `FAIL: Python 3.13 is required`; `active_python_files: 286`, `backup_layout: EMPTY_OR_NOT_PLACED`, `scope: SCAFFOLD_WORKSPACE_ONLY`.
- `git diff --check` → `PASS` (yalnız mevcut CRLF dönüşüm uyarıları).
- Live/testnet, credential, optimizer, economic result ve dış ağ yolu açılmadı.

## Açık kanıt gereksinimi

P1.16.g başlamadan önce local feature/indicator pipeline’ın hangi barları kullandığı, lookback/warmup başlangıcı, closed-bar zamanı, label future horizon ve historical runner’a bağlanma noktası gerçek kod/fixture üzerinden gösterilmelidir. Bu kanıt olmadan numeric purge/embargo veya warmup policy seçilmeyecek.

## Araştırma dayanağı

`docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md` warmup sırasında trading yapılmamasını ve warmup event’lerinin fill oluşturmamasını ister; aynı belge exact purge/embargo değerini local feature/label/event horizon bilgisine bağlar. Bu karar mevcut saf gate’in sınırını korur ve end-to-end iddiayı doğrulanmamış bırakır.
