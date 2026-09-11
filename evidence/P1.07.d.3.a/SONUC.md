# P1.07.d.3.a — BASE-only local reducer binding kanıtı

## Durum

COMPLETE_WITH_LIMITATION / LOCAL_PASS; bağımsız review: NOT_RUN.

Araştırma girdisi: docs/External_Claim_Verification/01_rapor/Ayrintili_Arastirma_Raporu.md.

Bu mikro fazda yalnız d.1 strict fixed-limit observation’ı ile mevcut core reducer arasında internal BASE-only bir application probe kuruldu. Public profile, HTTP response, persistence, UI, marker, SAFETY, EXIT ve yeni reserve formülü eklenmedi.

## Uygulanan sınır

src/dcabot/application/historical_base_limit_binding.py şu akışı yürütür:

~~~text
BASE fixed-limit order
→ immutable placement identity
→ d.1 historical observation
→ synthetic fill candidate
→ existing core INTENT/FILL/ORDER_FINAL
→ core position/leaves/anchor state
~~~

Adapter yalnız BUY ve config’teki exact base_qty ile eşleşen BASE order kabul eder. Equality observation ekonomik fill üretmez; placement barı değerlendirilmez; ambiguity barında yeni action commit edilmez; EOF’de pending order final/cancel/fill ile kapatılmaz. Strict candidate’lar exact declared limit fiyatı ve config’in mevcut fee pipeline’ı üzerinden core reducer’a gönderilir.

Probe sonucu açıkça reserve_model=NONE ve production_ready=false taşır. Mevcut core’da ayrı pending reserve bakiyesi bulunmadığı için bu sonuç production DCA risk/reserve kanıtı değildir.

## RED → GREEN

İlk RED kontrolünde yeni probe modülü bulunmadığı için 5 test import hatası verdi:

ModuleNotFoundError: No module named dcabot.application.historical_base_limit_binding

Minimum implementation sonrasında probe testleri 6/6 PASS verdi.

## Kanıtlanan davranışlar

1. Üç strict penetration barında BASE fixed slices 0.4 + 0.4 + 0.2 olarak core’a post edildi.
2. Core position quantity 1, order leaves 0, BASE anchor 100 ve exact fee 1/10 oldu.
3. Equality touch yalnız observation olarak kaldı; position ve anchor değişmedi.
4. Placement barı strict penetration içerse de fill oluşmadı.
5. Ambiguous bar öncesindeki bir strict fill korundu; ambiguity barında yeni fill oluşmadı.
6. BASE-only sınırı SELL order’ı BASE_SIDE_REQUIRED ile reddetti.
7. Pending BASE order varken ikinci core INTENT reddedildi.

## Mevcut core ile farklı kontrol

Bu probe testlerinin yanında mevcut core/store testleri duplicate execution, conflicting execution, overfill, late fill, partial coverage, safety blocker, exact leaves ve persistence audit davranışlarını kontrol ediyor. Bunlar probe’un expected değerini üretmek için kullanılmadı; ayrı event/store yollarıdır.

Son doğrulama:

- BASE-only probe: 6/6 PASS
- Tam Python regresyonu: 131/131 PASS
- compileall: PASS
- tools/check_workspace.py: PASS
- External research oracle: 48 PASS, kapsamı yalnız araştırma aritmetiği

## Açık kapılar

- Reserve acquisition/reduction/release/EOF lifecycle: LOCAL-CODE-REQUIRED / KANIT YOK
- Pending commitment ile local initial-margin estimate ayrımı: açık
- BASE anchor event’inin production binding için nihai sözleşmesi: bu probe’da core event’iyle gözlendi, bağımsız product acceptance’ı değil
- Duplicate candidate identity ile core execution identity arasındaki tam sözleşme: public binding için açık
- SAFETY ve EXIT binding: ayrı faz, DEFER

## Sonraki tek iş

P1.07.d.3.b — reserve lifecycle ve BASE commitment acceptance araştırması. Bu kapı kapanmadan probe public/API/persistence katmanına açılmayacak ve SAFETY/EXIT binding yapılmayacaktır.
