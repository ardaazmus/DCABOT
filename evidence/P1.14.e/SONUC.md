# P1.14.e — Strategy template integrity ve non-authority

## Sonuç

- Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Kod: `src/dcabot/application/strategy_template.py`
- Test: `tests/test_strategy_template.py`
- Bağımsız review: `NOT_RUN`
- Production readiness: `NO`
- Sonraki tek iş: `P1.14.f` template activation/capability gate karar kapısı

Bu mikro-fazda strategy template, yalnızca doğrulanmış ve değişmez bir configuration artifact olarak modellenmiştir. Template import’u activation, candidate, order, reserve veya fill authority’si taşımaz.

## Uygulanan sözleşme

- Yalnız `strategy-template-v1` kabul edilir.
- Payload canonical JSON olarak `sort_keys`, sabit ayraçlar ve `allow_nan=false` ile saklanır.
- Payload SHA-256 canonical snapshot’a bağlıdır; hash mismatch ve canonical olmayan snapshot reddedilir.
- Payload boyutu 64 KiB ile sınırlandırılmıştır; nesting bounded’dir.
- Float, executable/script/command/code ve secret/credential/token alanları reddedilir.
- `declared_capabilities` identifier olarak doğrulanır, duplicate reddedilir ve canonical sıraya alınır.
- Template üzerinde activation veya order/fill metodu bulunmaz.

## Bilinçli kapsam dışı

Template’in payload hash’ini dış bir webhook body’sinden üretme, imza/auth, capability’nin stratejiye bağlanması, activation approval, parameter validation against a selected profile, order/reserve/fill, persistence, API ve UI eklenmedi. Imported template ekonomik otorite değildir.

## Kontroller

- Önce test RED: yeni test dosyası eksik `strategy_template` modülü nedeniyle import error verdi.
- En küçük uygulama sonrası kanonik `uv run --frozen python tools/run_checks.py`: `286/286 PASS`.
- Bağımsız canonical/hash/non-authority control: mapping/capability sırası değişmezliği ve snapshot hash eşleşmesi `PASS`.
- Bağımsız kontrolde ilk command quoting hatası düzeltildi; düzeltilmiş kontrol `PASS`.
- `uv run --frozen python -m compileall -q src tests`: `PASS`.
- `uv run --frozen python tools/check_workspace.py`: `PASS`; `120` aktif Python dosyası; backup discovery kapsam dışı.

## Kanıt sınırı

Araştırma kanıtı `docs/P1_KRITIK_ARASTIRMA_FINAL/11_P1.14_REBALANCING_SIGNAL_TEMPLATES.md` template version/hash/capability ve doğrudan order authority’nin reddini destekliyor; yerel implementation’ın geçtiğini iddia etmiyor. Bu teslim yalnız artifact integrity ve non-authority kabulüdür.
