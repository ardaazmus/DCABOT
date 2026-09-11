# P1.10.b — Multi-TP exact quantity conservation sonucu

## Karar

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`.

P1.10 araştırmasındaki multi-TP kapasite invariant’ı saf application validation contract’ı olarak eklendi. Açık pozisyon miktarı; kabul edilmiş exit fill’leri ve hâlen committed olan exit miktarıyla aşılmadığı sürece kalan free exit capacity exact olarak hesaplanıyor.

## Uygulanan sınır

- `open_qty` pozitif exact decimal miktar olarak doğrulanır.
- `accepted_exit_fills` ve `committed_exit_qty` ayrı tuple’lar olarak exact toplanır.
- `free_exit_capacity = open_qty - accepted_exit_fills - committed_exit_qty` exact hesaplanır.
- Toplam tüketim açık pozisyonu aşarsa `EXIT_CAPACITY_EXCEEDED` ile fail-closed reddedilir.
- Kısmi fill’in committed girdisi yalnız kalan commitment olmalıdır; ilk talep miktarının tekrar sayılması bu contract’a dahil edilmez.
- Contract yalnız validation projection’dır; order kabulü, cancel, fill, reserve veya position mutation yapmaz.

## Kanıt zinciri

Yeni uygulama kodundan önce testler çalıştırıldı ve modül bulunamadığı için RED alındı:

```text
ModuleNotFoundError: dcabot.application.multi_tp_conservation
```

Uygulama eklendikten sonra GREEN:

```text
Ran 4 tests ... OK
```

Over-close reddi, exact kalan kapasite, split-fill conservation ve malformed/zero input kontrolleri geçildi.

Bağımsız Python 3.13 suite’i:

```text
Ran 7 tests ... OK
```

Tam regresyon:

```text
Ran 205 tests ... OK
```

Compile/workspace:

```text
status: PASS
errors: []
active_python_files: 91
backup_layout: EMPTY_OR_NOT_PLACED
scope: SCAFFOLD_WORKSPACE_ONLY
```

## Açık sınırlar

- Contract henüz core `State.orders` içine multi-TP order registry olarak bağlanmadı.
- OCO/competing exit, cancel-replace, late fill, stop-market/stop-limit, trailing, breakeven, API/UI, persistence, reserve ve live/testnet yoktur.
- P1.10 tamamlanmış sayılmaz; sıradaki tek iş P1.10.c stop trigger/execution ayrımının local contract kontrolüdür.

