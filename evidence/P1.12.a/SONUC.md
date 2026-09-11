# P1.12.a — Linear futures PnL ve funding temel sınırı

## Durum

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`; production readiness `NO`.

## Uygulanan en küçük davranış

`src/dcabot/application/linear_futures_math.py` içinde spot state’inden ayrı, saf bir linear futures projection eklendi:

- `LONG` ve `SHORT` yönleri discriminated biçimde doğrulanır.
- Contract quantity ile base-equivalent miktar arasındaki ilişki `contract_size` alanıyla explicit tutulur; sessizce `1` varsayılmaz.
- `position_value = effective_quantity × mark_price` settlement asset bağlamında hesaplanır.
- `UPL_long = Q_effective × (mark - entry)` ve `UPL_short = Q_effective × (entry - mark)` exact hesaplanır.
- Funding, timestamp taşıyan ayrı bir projection’dır; pozitif rate long için gider (`negative amount`), short için gelir (`positive amount`), negatif rate yönü tersine çevirir.
- Finansal girişler decimal string, ekonomik hesaplar `Fraction`, çıktılar exact decimal string’dir.

Kaldıraç, initial/maintenance margin, isolated/cross, liquidation, mark/index feed adapter, persistence, API/UI, venue execution ve gerçek account binding bu mikro fazda açılmadı.

## Doğrulama zinciri

- RED: modül yokken yeni suite import failure; mevcut 241 test korunuyordu.
- GREEN: `tests/test_linear_futures_math.py` ile tam regresyon `245/245 PASS`.
- Bağımsız kontrol: production import etmeden Decimal oracle `PASS`; Q=1.25, entry=40000, mark=42000 için long `2500`, short `-2500`, funding absolute `5.2500`.
- Workspace/compile: `uv run --frozen python tools/check_workspace.py` → `PASS`; `104` aktif Python dosyası.
- Negative kontrol: invalid side, unsafe settlement asset ve negatif funding event time fail-closed reddedildi.

## Araştırma temeli

`docs/P1_KRITIK_ARASTIRMA_FINAL/09_P1.12_FUTURES_MODEL.md` linear PnL, funding ve partial-close ayrımını `ACCEPT`; margin kapsamını `DEFER`; liquidation’ı venue-profile yokluğunda `BLOCKED/DEFER` olarak sınıflandırıyor. Uygulama yalnız kabul edilen linear PnL/funding çekirdeğini taşır.

## Açık sınır ve üretim kararı

Bu projection mevcut CORE01 spot/long state’ine bağlanmadı ve bir venue’un kapalı risk motorunu temsil etmez. Funding schedule/rate dataset’i yoksa olay sentezlenemez. Contract multiplier, settlement asset, fee asset, mark authority ve profile version olmadan yeni ekonomik risk açılmaz. Margin veya liquidation için generic formül eklenmeyecek.

## Sonraki tek iş

`P1.12.b` — linear futures partial-close, trading fee/funding ledger ve event/replay contract karar kapısı; margin/liquidation ayrı profile gate olarak korunacak.
