# P1.15.a — Hedge identity ve two-leg state sınırı

## Sonuç

- Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Kod: `src/dcabot/application/hedge_two_leg_contract.py`
- Test: `tests/test_hedge_two_leg_contract.py`
- Bağımsız review: `PASS` (Herschel salt-okunur Codex incelemesi, düzeltme sonrası)
- Production readiness: `NO`
- Sonraki tek iş: `P1.15.b` two-leg accepted-fill/recovery projection karar kapısı

P1.15 araştırmasındaki kabul edilebilir alt kapsamdan yalnız position identity ve iki-bacak lifecycle sınırı uygulandı. `ONE_WAY` ile `HEDGE` kimlikleri ayrıdır; hedge kimliği `LONG`/`SHORT` side taşır. İki-bacak state’i `NONE`, `LEG_A_PENDING`, `ONE_LEG_FILLED`, `PARTIAL_HEDGE`, `BOTH_ESTABLISHED`, `RECOVERY_REQUIRED` ve `TIMEOUT` olarak explicit tutulur.

## Uygulanan sözleşme

- Identity account, versioned venue profile, product, symbol, position mode ve gerekiyorsa hedge side ile immutable’dır.
- `ONE_WAY` identity hedge side kabul etmez; `HEDGE` identity side olmadan kabul edilmez.
- First-leg accepted/partial fill ara durumları ekonomik olarak görünür state’tir; rollback veya fake atomicity yoktur.
- Yalnız açık geçişler kabul edilir. `ONE_LEG_FILLED` veya `PARTIAL_HEDGE` içinden `RECOVERY_REQUIRED` ve `TIMEOUT` mümkündür.
- `BOTH_ESTABLISHED` yalnız açık `BOTH_LEGS_ACCEPTED` event’i ile oluşur; miktar dengesi, fee, funding, margin, liquidation veya cross conversion bu fazda hesaplanmaz.
- Modül order, reserve, fill posting, persistence, venue adapter veya API/UI authority taşımaz.

## Bilinçli kapsam dışı ve blokajlar

Two-leg accepted-fill miktar projection’ı, duplicate/replay persistence, recovery ledger, cross-account capacity, reduce-only venue adapter, one-leg liquidation ve venue-specific margin/liquidation hesapları sonraki karar kapılarıdır. `test_matrices/P1.15_TESTS.md` bu checkout’ta bulunmadığı için bu fazda yalnız mevcut araştırma matrisinin dar kimlik/state alt kümesi test edildi. Venue-specific numeric profile seçilmeden liquidation/cross formülü eklenmedi.

## Kontroller

- Bağımsız review’da eşitlenen fakat hashlenemeyen custom state girdisinin
  transition dictionary’sine ulaşarak ham `TypeError` üretebildiği bulundu.
  Önce regresyon `1` error verdi; `advance_two_leg_state` girişine explicit
  string guard eklendi ve fail-closed `TWO_LEG_STATE_INVALID` ile düzeltildi.
- Güncel odak `python -m unittest tests.test_hedge_two_leg_contract`: `4/4 PASS`.
- İlgili two-leg projection kümesi `python -m unittest tests.test_hedge_two_leg_contract tests.test_two_leg_fill_projection`: `8/8 PASS`.
- Bağımsız hedge/two-leg oracle: identity ayrımı, frozen scope, whitelist
  geçişleri, partial/one-leg/recovery/timeout ve unhashable state reddi `PASS`.
- Herschel salt-okunur Codex review düzeltme sonrası: `PASS`; kritik P1/P2
  bulgu yok. Review’da `test_matrices/P1.15_TESTS.md` varlık iddiası kontrol
  edildi ve bu checkout’ta dosyanın bulunmadığı doğrulandı; araştırma belgesi
  tarihsel girdidir ve değiştirilmedi.
- `python -m compileall -q src`: `PASS`; `git diff --check`: `PASS`.
- `tools/run_checks.py` güncel tam-suite için `FAIL`: proje `Python 3.13`
  isterken kullanılabilir bundled runtime `3.12.14`; bu nedenle güncel
  tam-suite sonucu iddia edilmiyor.
- Önceki tarihsel tam-suite sonucu (`294/294`) bu oturumun doğrulaması olarak kullanılmadı.
- Live/testnet, credential ve gerçek emir yolu açılmadı.

## Kanıt sınırı

`docs/P1_KRITIK_ARASTIRMA_FINAL/12_P1.15_HEDGE_CROSS_TWO_LEG.md` one-way/hedge identity ayrımını ve two-leg intermediate state’lerini kabul eder; recovery, cross ownership ve venue-specific liquidation’ı DEFER eder. Bu teslim yalnız ilk iki kabulü yerel testlerle doğrular; P1.15’in tamamlandığını iddia etmez.
