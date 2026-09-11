# P1.10.e — Trailing exit capacity binding sonucu

## Karar

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`.

Tetiklenmiş long trailing state, exact multi-TP exit capacity contract’ına bağlandı. Yeni trailing exit adayı; accepted fill’ler, mevcut commitment’lar ve aday miktarı birlikte açık pozisyonu aşmıyorsa yalnız validation projection olarak döner.

## Uygulanan sınır

- Sadece `TRIGGERED` trailing state aday üretebilir.
- Trigger fiyatı trailing state’in exact `stop_price` değeridir.
- Yeni aday miktarı mevcut commitment’lara eklenerek `free_exit_capacity` yeniden hesaplanır.
- Over-close `EXIT_CAPACITY_EXCEEDED` ile fail-closed reddedilir.
- Sonuç `order_authority=NONE` taşır; order kabulü, reserve, cancel, fill ve position mutation yapılmaz.
- Tetiklenmemiş trailing state’ten exit adayı üretilemez.

## Kanıt zinciri

Yeni uygulama kodundan önce testler çalıştırıldı ve binding modülü bulunamadığı için RED alındı:

```text
ModuleNotFoundError: dcabot.application.trailing_exit_binding
```

GREEN sonrası:

```text
Trailing-exit binding: Ran 3 tests ... OK
```

Bağımsız Python 3.13 ilgili suite’i:

```text
Ran 12 tests ... OK
```

Tam regresyon:

```text
Ran 216 tests ... OK
```

Compile/workspace:

```text
status: PASS
errors: []
active_python_files: 96
backup_layout: EMPTY_OR_NOT_PLACED
scope: SCAFFOLD_WORKSPACE_ONLY
```

## Açık sınırlar

- Binding tek long trailing projection’ıdır; short/percentage trailing ve venue-specific execution yoktur.
- OCO/competing exit, cancel-replace, late fill, stop-market/stop-limit, gap/slippage, breakeven, API/UI, persistence, reserve ve live/testnet yoktur.
- P1.10 tamamlanmış sayılmaz; sıradaki tek iş P1.10.f breakeven koşul/fee dönüşüm karar kapısıdır.

