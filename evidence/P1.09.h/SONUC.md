# P1.09.h — Bağımsız exact/metamorphic sizing oracle sonucu

## Karar

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`.

Bu mikro-fazda production davranışı değiştirilmedi. Mevcut sizing zincirini bağımsız bir Decimal oracle ve metamorphic kontrollerle sınayan test-only kanıt eklendi. Test geçişi order authority, reserve, risk kabulü veya economic posting yetkisi vermez.

## Uygulanan kontroller

- QUOTE_NOTIONAL candidate quantity bağımsız `Decimal(notional) / Decimal(price)` hesabıyla eşleştirildi.
- Eşdeğer decimal yazımları (`0.4`/`0.40`, `250`/`250.00`) aynı candidate sonucunu üretmelidir.
- Aynı allocation kümesinin sıralanması conservation sonucunu değiştirmemelidir.
- Ladder fiyatları bağımsız `anchor * (1 - deviation * index)` formülüyle karşılaştırıldı.
- QUOTE_NOTIONAL ladder allocation değerleri bağımsız beklenen exact tabloyla karşılaştırıldı.

## Kanıt zinciri

### RED

Uygulanacak production değişikliği bulunmadığı için import-failure RED uygulanmadı. Bu, mevcut davranışın bağımsız testle sınandığı test-only bir mikro-fazdır.

### GREEN

```text
Ran 197 tests ... OK
```

Yeni test dosyası ayrıca bağımsız hedef olarak çalıştırıldı:

```text
Ran 3 tests ... OK
```

### Farklı kontrol

Python 3.13 ile `compileall` ve `tools/check_workspace.py` çalıştırıldı:

```text
status: PASS
errors: []
active_python_files: 88
backup_layout: EMPTY_OR_NOT_PLACED
scope: SCAFFOLD_WORKSPACE_ONLY
```

## Sınırlar ve karar

- Oracle yalnız P1.09.a–g’deki exact sizing çıktısını sınar; yeni BASE↔QUOTE conversion yolu, balance discovery, venue quantization, risk, reserve, API/UI, persistence ve economic posting eklenmedi.
- `order_authority=NONE` ve public sizing akışının kapalı kalması korunur.
- P1.09.h tamamlandı; sıradaki tek iş P1.09.i için bağımlılık/uygulama kapısıdır.

