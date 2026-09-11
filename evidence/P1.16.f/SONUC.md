# P1.16.f — Warmup leakage ve readiness binding karar kapısı

## Karar

- Durum: `DEFERRED / NO-GO / LOCAL_PASS`
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

## Kontroller

- Mevcut kanıt yeniden doğrulandı: `uv run --frozen python tools/run_checks.py` → `318/318 PASS`.
- `uv run --frozen python -m compileall -q src tests` → `PASS`.
- `uv run --frozen python tools/check_workspace.py` → `PASS`; `136` aktif Python dosyası.
- Live/testnet, credential, optimizer, economic result ve dış ağ yolu açılmadı.

## Açık kanıt gereksinimi

P1.16.g başlamadan önce local feature/indicator pipeline’ın hangi barları kullandığı, lookback/warmup başlangıcı, closed-bar zamanı, label future horizon ve historical runner’a bağlanma noktası gerçek kod/fixture üzerinden gösterilmelidir. Bu kanıt olmadan numeric purge/embargo veya warmup policy seçilmeyecek.

## Araştırma dayanağı

`docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md` warmup sırasında trading yapılmamasını ve warmup event’lerinin fill oluşturmamasını ister; aynı belge exact purge/embargo değerini local feature/label/event horizon bilgisine bağlar. Bu karar mevcut saf gate’in sınırını korur ve end-to-end iddiayı doğrulanmamış bırakır.
