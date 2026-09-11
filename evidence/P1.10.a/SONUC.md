# P1.10.a — Exit trigger/execution boundary sonucu

## Karar

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`.

P1.10 araştırmasındaki `trigger != execution` ayrımı mevcut long-only core reducer üzerinde bağımsız testlerle doğrulandı. TP trigger’ı yalnız karar/observation üretir; position, realized veya fee ancak ayrı execution olaylarıyla değişir.

## Kanıtlanan davranış

- TP eşiğine gelen mark, `("EXIT", qty)` kararı üretir; karar çağrısı ekonomik state’i değiştirmez.
- `EXIT` `INTENT` kabulü açık order oluşturur, fakat pozisyonu veya realized sonucu değiştirmez.
- `SELL` `FILL` kabulü position’ı azaltan ve realized/fee alanlarını değiştiren ekonomik geçiştir.
- Exact qty ve fee değerleri mevcut Fraction tabanlı core üzerinden doğrulandı.

## Kanıt zinciri

Bu mikro-faz test-only olduğundan yeni production davranışı eklenmedi ve import-failure RED uygulanmadı.

Odak boundary suite’i:

```text
Ran 3 tests ... OK
```

Mevcut engine davranışına farklı odak kontrolü:

```text
Ran 1 test ... OK
```

Tam regresyon:

```text
Ran 201 tests ... OK
```

Python 3.13 ile compile/workspace kontrolü:

```text
status: PASS
errors: []
active_python_files: 89
backup_layout: EMPTY_OR_NOT_PLACED
scope: SCAFFOLD_WORKSPACE_ONLY
```

## Açık sınırlar

- Multi-TP conservation, stop-market/stop-limit ayrıntısı, trailing ratchet, breakeven, cancel-replace ve late-fill recovery bu mikro-fazda uygulanmadı.
- Historical adapter’ın aynı bar içi belirsizlik davranışı ayrıca korunur; bu testler onu genişletmez.
- API/UI, persistence, reserve, venue/testnet/live ve yeni ekonomik model eklenmedi.
- P1.10 fazı tamamlanmış sayılmaz; sıradaki küçük iş multi-TP quantity conservation için local core contract kontrolüdür.

