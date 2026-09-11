# P1.09.d — Tagged eligible-balance percent budget sonucu

## Karar

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`.

P1.09 araştırmasındaki balance-percent formülü, gerçek hesap bakiyesi keşfetmeden ve total/available/reserved alanlarını karıştırmadan caller-supplied eligible balance projection’ı olarak uygulandı.

## Uygulanan davranış

`build_balance_percent_budget` şu açık girdileri zorunlu kılar:

- `balance_source`: bakiyenin hangi açık kaynaktan geldiğini belirten kimlik;
- `asset`: büyük harfli asset kodu;
- `eligible_balance`: pozitif exact decimal string;
- `percent`: `0 < percent <= 1` aralığında exact decimal string.

Budget exact olarak `eligible_balance * percent` ile hesaplanır ve tüm sonuç alanları canonical decimal string olarak döndürülür. Kaynak, asset, numeric format, zero balance veya yüzde sınırı geçersizse fail-closed hata döner.

Bu projection balance fetch etmez, reserve oluşturmaz, mevcut reserve’i düşmez, risk kabulü yapmaz ve ekonomik order post etmez.

## Kanıt zinciri

### RED

Yeni `tests/test_balance_percent_sizing.py`, henüz mevcut olmayan `dcabot.application.balance_percent_sizing` modülünü import ettiği için test discovery aşamasında `ModuleNotFoundError` verdi.

### GREEN

`src/dcabot/application/balance_percent_sizing.py` eklendikten sonra proje kontrolü:

```text
Ran 185 tests ... OK
```

Odak testleri `1000 * 0.25 = 250` exact budget’ını, kaynak/asset/percent/zero input sınırlarını ve fail-closed davranışı doğrular.

### Farklı kontrol

Balance-percent suite’i doğru `src` import yolu ile bağımsız unittest hedefi olarak `3/3 PASS` geçti. `compileall` ve `tools/check_workspace.py` de PASS verdi.

## Açık sınırlar

- `balance_source` yalnız etiket zorunluluğudur; gerçek account veya wallet authority’si değildir.
- Total, available, reserved, credit ve settled bakiyenin seçimi bu mikro fazda çözülmedi.
- Reserve lifecycle, risk/exposure, ladder binding, venue quantization, API/UI, persistence ve economic posting yoktur.
- P1.09.e’de ladder generation’ın bu contract’lara bağlanması ele alınacaktır.
