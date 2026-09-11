# P1.15.a — Hedge identity ve two-leg state sınırı

## Sonuç

- Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Kod: `src/dcabot/application/hedge_two_leg_contract.py`
- Test: `tests/test_hedge_two_leg_contract.py`
- Bağımsız review: `NOT_RUN`
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

- Önce test RED: yeni test dosyası eksik `hedge_two_leg_contract` modülü nedeniyle beklenen import error verdi; suite `291` testte kaldı.
- En küçük uygulama sonrası `uv run --frozen python tools/run_checks.py`: `294/294 PASS`.
- Bağımsız hedge/two-leg control: identity ayrımı, first-leg state, partial hedge ve recovery geçişleri `PASS`.
- `uv run --frozen python -m compileall -q src tests`: `PASS`.
- `uv run --frozen python tools/check_workspace.py`: `PASS`; `124` aktif Python dosyası.
- Live/testnet, credential ve gerçek emir yolu açılmadı.

## Kanıt sınırı

`docs/P1_KRITIK_ARASTIRMA_FINAL/12_P1.15_HEDGE_CROSS_TWO_LEG.md` one-way/hedge identity ayrımını ve two-leg intermediate state’lerini kabul eder; recovery, cross ownership ve venue-specific liquidation’ı DEFER eder. Bu teslim yalnız ilk iki kabulü yerel testlerle doğrular; P1.15’in tamamlandığını iddia etmez.
