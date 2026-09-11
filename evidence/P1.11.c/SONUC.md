# P1.11.c — Account reservation capacity/version projection

## Durum

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`; production readiness `NO`.

## Uygulanan en küçük davranış

`src/dcabot/application/account_reservation.py` içinde yalnız saf, mutation yapmayan bir account reservation projection sınırı eklendi:

- `AccountCapacity`, tek account ve tek açık asset için pozitif exact kapasite ile non-negative account version taşır.
- `AccountReservation`, reservation kimliğini ve `SharedAccountIdentity` sahibini immutable biçimde taşır.
- Aynı account ve asset kapsamındaki aktif reservation miktarları exact toplanır.
- `available = capacity - Σactive_reservations` hesaplanır; kapasite aşımı fail-closed reddedilir.
- Duplicate reservation ID, cross-account/cross-asset kayıt ve stale `expected_version` reddedilir.
- Başarılı aday projection `version_before` ve `version_after = version_before + 1` ile döner.
- Economic posting, order/position mutation ve UI hesabı yoktur.

## Doğrulama zinciri

- RED: modül henüz yokken import failure.
- GREEN: `tests/test_account_reservation.py` `5/5 PASS`.
- Farklı bağımsız kontrol: production import etmeden Fraction oracle `PASS` (kapasite `100`, aktif `20`, istek `30` → kalan `50`, version `+1`).
- Tam regresyon: `uv run --frozen python tools/run_checks.py` → `236/236 PASS`.
- Compile/workspace: `uv run --frozen python tools/check_workspace.py` → `PASS`; `100` aktif Python dosyası.

## Araştırma temeli

`docs/P1_KRITIK_ARASTIRMA_FINAL/08_P1.11_SHARED_ACCOUNT.md` account-level ownership, exact reservation invariant ve version-conflict gereksinimini destekler; ancak transaction/locking, persistence/replay ve fill/release yerel kod kanıtı ister.

## Açık sınır

Bu modül committed ledger değildir; yalnız aday projection üretir. SQLite transaction/locking ile gerçek multi-writer atomikliği, restart/replay, reservation release/fill dönüşümleri, dedup, API/UI authority ve cross-deal izolasyon bu mikro fazda açılmadı. Bu nedenle production reservation readiness `NO` olarak kalır.

## Sonraki tek iş

`P1.11.d` — atomic reservation persistence/replay ve reservation fill/release karar kapısı.
