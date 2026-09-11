# P1.09.i — BASE adayının quote commitment gate’e bağlanması

## Karar

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`.

P1.09.a’da exact olarak hesaplanan `BASE_QTY` adayının, açık referans fiyatla üretilmiş quote notional’ı üzerinden mevcut quote-unit pre-acceptance gate’e alınması doğrulandı. Bu geçiş order authority, reserve veya economic posting vermez.

## Uygulanan en küçük değişiklik

- Gate artık `BASE_QTY` ve `QUOTE_NOTIONAL` candidate türlerini kabul eder.
- Candidate quantity × explicit reference price sonucu candidate notional ile eşleşmiyorsa mevcut fail-closed conflict korunur.
- Ladder allocation ve eligible budget hâlâ yalnız `QUOTE_NOTIONAL` biriminde kalır.
- Candidate/ladder unit çatışması, quote asset çatışması, profile filter ve toplam budget sınırı korunur.
- Geçen sonuçta `order_authority=NONE` korunur; accepted intent, reserve, persistence, API/UI ve economic posting açılmaz.

## Kanıt zinciri

### RED

Yeni BASE kabul testi önce eklendi. Mevcut gate, `BASE_QTY` adayını `PRE_ACCEPTANCE_UNIT_CONFLICT` ile reddetti:

```text
Ran 4 tests ... FAILED (errors=1)
PRE_ACCEPTANCE_UNIT_CONFLICT
```

### GREEN

Unit kabul koşulu yalnız desteklenen iki candidate türünü kapsayacak şekilde genişletildikten sonra:

```text
Ran 4 tests ... OK
Ran 198 tests ... OK
```

### Farklı kontrol

Bağımsız ilgili suite çalıştırıldı:

```text
Ran 9 tests ... OK
```

Python 3.13 ile `compileall` ve `tools/check_workspace.py`:

```text
status: PASS
errors: []
active_python_files: 88
backup_layout: EMPTY_OR_NOT_PLACED
scope: SCAFFOLD_WORKSPACE_ONLY
```

## Açık sınırlar

- BASE adayının gate’e alınması, venue quantization/rounding owner kararı veya live/testnet emir desteği değildir.
- Balance discovery, multi-asset conversion, risk acceptance, reserve lifecycle, persistence, API/UI ve economic posting kapsam dışıdır.
- P1.09 sizing zincirinin sonraki güvenli işi plan bağımlılıkları kontrol edilerek seçilecektir; P1.10’a geçiş P1.09 kapsamının tamamlandığı anlamına gelmez.

