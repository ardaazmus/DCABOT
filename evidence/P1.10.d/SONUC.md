# P1.10.d — Long trailing ratchet sonucu

## Karar

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`.

Araştırmadaki trailing state ve monotonic ratchet davranışı, sabit mesafeli long trigger projection olarak uygulandı. Contract yalnız state/trigger üretir; execution, fill, position veya PnL mutation yapmaz.

## Uygulanan sınır

- `INACTIVE` state aktivasyon fiyatının altında kalır.
- Aktivasyonla birlikte `high_water = observed_price` ve `stop_price = high_water - distance` exact hesaplanır.
- Yeni lehte high-water stop’u yukarı ratchet eder.
- Geri çekilme stop fiyatını aşağı indirmez.
- Gözlem stop’a eşit veya altında olduğunda state `TRIGGERED` olur.
- Tetiklenmiş state yeniden gözlenemez; invalid activation/distance/price fail-closed reddedilir.

## Kanıt zinciri

Yeni production modülünden önce testler çalıştırıldı ve modül bulunamadığı için RED alındı:

```text
ModuleNotFoundError: dcabot.application.trailing_ratchet
```

GREEN sonrası trailing suite:

```text
Ran 5 tests ... OK
```

Aktivasyon altı pasiflik, exact stop hesabı, favorable ratchet, retracement monotonicity, trigger sınırı ve invalid state kontrolleri geçti.

Bağımsız Python 3.13 TP/STOP/trailing/multi-TP suite’i:

```text
Ran 15 tests ... OK
```

Tam regresyon:

```text
Ran 213 tests ... OK
```

Compile/workspace:

```text
status: PASS
errors: []
active_python_files: 94
backup_layout: EMPTY_OR_NOT_PLACED
scope: SCAFFOLD_WORKSPACE_ONLY
```

## Açık sınırlar

- Yalnız long + sabit absolute distance desteklenir; percentage distance, short trailing, venue-specific activation, stop-market/stop-limit ve gap/slippage yoktur.
- `TRIGGERED` sonucu execution order veya fill değildir.
- API/UI, persistence, reserve, OCO/cancel-replace, late fill, breakeven ve live/testnet yoktur.
- P1.10 tamamlanmış sayılmaz; sıradaki tek iş P1.10.e trailing state’in exit capacity/trigger boundary ile birlikte kontrolüdür.

