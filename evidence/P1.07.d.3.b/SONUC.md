# P1.07.d.3.b — Reserve lifecycle ve BASE commitment kanıtı

## Durum

`RESEARCH_RECEIVED / SIMPLIFY_WITH_LIMITATION`; bağımsız review: `NOT_RUN`.

Araştırma girdisi: `C:\Users\nefer\Downloads\P1.07.d.3.b_Reserve_Lifecycle_Ayrintili_Arastirma_Raporu.md`.

Rapor talimat olarak değil, reserve ve commitment iddialarını değerlendirmek için kanıt kaynağı olarak işlendi. Nihai karar ikiye ayrıldı:

- Mevcut BASE-only v1: `SIMPLIFY`; `reserve_model=NONE` açık sınır olarak korunur.
- Yeni sayısal reserve ledger’ı: `DEFER`; asset/unit, acquisition/reduction/release owner, fee, partial fill, EOF, ambiguity, duplicate/late ve atomicity sözleşmeleri yerel kod/test ile kapanmadan eklenmez.

## Yerel kanıtla kontrol

| İddia | Yerel kontrol | Sonuç |
|---|---|---|
| Initial-margin estimate ayrı reserve ledger’ıdır | `engine.py` INTENT dalı ve `State` alanları incelendi | Doğrulanmadı; estimate yalnız kabul kontrolü, persistent reserve alanı yok |
| BASE pending blocker reserve yerine lifecycle gate olabilir | core `unsettled` kontrolü + d.3.a pending BASE testi | Doğrulandı; ikinci BASE reddediliyor |
| Equality ve placement barı ekonomik fill üretmez | fixed-limit ve BASE binding testleri | Doğrulandı |
| Strict candidate yalnız core FILL üzerinden ekonomik state’i etkiler | d.3.a adapter zinciri ve exact partial testleri | Sınır içinde doğrulandı; ayrı candidate event/state yok |
| Ambiguity committed prefix’i geri almaz | d.3.a ambiguity testi | Doğrulandı |
| EOF pending order’ı sentetik cancel/fill/final yapmaz | fixed-limit EOF testleri | Doğrulandı; `OPEN_AT_END` |
| Duplicate/late güvenliği tamamen reducer seviyesinde kapanmıştır | core reducer ve store testleri ayrı incelendi | Kısmen doğrulandı; store dedupe var, saf reducer `execution_id` idempotency’si yok; late-fill blocker mevcut |
| Reserve public/production için hazırdır | binding sonucu | Yanlış; probe `reserve_model=NONE`, `production_ready=false` taşır ve public/API/persistence’e bağlı değildir |

## Test → farklı kontrol → sonuç

- Reserve/BASE binding odak testleri, fixed-limit policy ve store/core lifecycle testleri birlikte çalıştırıldı: `37/37 PASS`.
- Farklı kontrol olarak tam `tools/run_checks.py` çalıştırıldı: `137/137 PASS`.
- `compileall src tests`: `PASS`.
- `tools/check_workspace.py`: `PASS`.

Bu sonuçlar mevcut davranışın rapordaki `NONE` sınırıyla uyumlu olduğunu gösterir; explicit reserve ledger’ın doğru olduğunu göstermez.

## Uygulanmayan değişiklikler

- Numeric `reserve_amount`, reserve asset/unit veya initial-margin → reserve dönüşümü eklenmedi.
- Candidate/equality zamanında reserve mutation eklenmedi.
- EOF release/cancel, fee conversion, reserve rounding veya late-fill recovery varsayılmadı.
- BASE probe public profile, API, persistence, UI veya production path’e açılmadı.
- SAFETY/EXIT reserve binding başlatılmadı.

## Açık kabul kapıları

1. `reserve_model=NONE` için remaining local acceptance testleri: numeric zero yerine açık `NOT_MODELED`/absence sınırı, pending SAFETY blocker, full-fill/final coverage ve legacy isolation.
2. Reducer/store replay sınırının açıkça ayrılması: bilinen duplicate no-op, conflicting duplicate ve yeni late fill için authority kaydı.
3. Bu kapılar GREEN olmadan public DCA limit contract’ı ve explicit reserve ledger açılmayacak.

## Sonraki tek iş

`P1.07.d.3.c — BASE-only reserve_model=NONE kabul testleri`: yalnız mevcut NONE politikasının eksik yerel acceptance testlerini RED → GREEN ile kapatmak. Bu işte sayısal reserve, public API, persistence, UI, SAFETY veya EXIT eklenmeyecek.
