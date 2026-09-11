# P1.16.g — Local feature/label horizon ve gerçek run binding karar kapısı

## Karar

- Durum: `DEFERRED / NO-GO / LOCAL_PASS`
- Kod değişikliği: yok
- Bağımsız review: `NOT_RUN`
- Production readiness: `NO`
- Sonraki tek iş: `P1.16.h` bounded real-run lineage binding karar kapısı

## Gerçek local bulgu

Kaynak ve test ağacında bağımsız bir feature/indicator/label pipeline, lookback hesaplayıcısı, label future horizon sözleşmesi veya bu veriyi historical runner’a bağlayan bir adapter bulunamadı. Mevcut tarihsel runner kapalı OHLCV barlarını doğrudan işler; `signal_readiness.py` ise yalnız event-time, closed-bar, stale ve caller tarafından verilen warmup sayısını sınıflandıran saf bir gate’tir.

Bu nedenle feature lookback, label future horizon, settlement horizon veya numeric purge/embargo değeri üretmek mümkün değildir. Bunlardan birini varsayarak kod yazmak veri sızıntısı riskini azaltmaz; aksine doğrulanmamış bir model varsayımını ekonomik akışa sokar.

## Uygulanmayan değişiklik

Yeni indicator/feature/label hesaplama, warmup sayısı, purge/embargo bar sayısı, run identity binding, OOS KPI, optimizer, persistence, API/UI ve ekonomik sonuç kodu açılmadı. Mevcut `TimeInterval` overlap gate’i korunuyor; gerçek horizon kaynağı olmadığı için yalnız `PURGE_REQUIRED`/`NO_OVERLAP` değerlendirmesiyle sınırlı.

## Kontroller

- Local source audit: feature/indicator/label pipeline ve historical runner binding bulunmadı; mevcut `signal_readiness.py` kapsamı ayrıca okundu.
- Mevcut kanıt yeniden doğrulandı: `uv run --frozen python tools/run_checks.py` → `318/318 PASS`.
- `uv run --frozen python -m compileall -q src tests` → `PASS`.
- `uv run --frozen python tools/check_workspace.py` → `PASS`; `136` aktif Python dosyası.
- Live/testnet, credential, optimizer, economic result ve dış ağ yolu açılmadı.

## Gerekli sonraki kanıt

Gerçek run binding’e geçmeden önce her feature’ın kullandığı geçmiş aralık, warmup başlangıcı, closed-bar kuralı, label’ın geleceğe taşan aralığı, settlement/observation horizon’ı ve bunların dataset/config/model identity’ye nasıl bağlandığı gerçek kod/fixture üzerinden gösterilmelidir. Bu kanıt gelmeden numeric purge/embargo seçilmeyecek.

## Araştırma dayanağı

`docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md` warmup event’lerinin fill üretmemesini ve purge/embargo değerinin local feature/label/event horizon bilgisine bağlı olduğunu belirtir. Bu karar kapısı, mevcut local kapsamın bu gereksinimleri taşımadığını doğrulayarak üretim kodunu güvenli biçimde erteledi.
