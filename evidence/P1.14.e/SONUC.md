# P1.14.e — Strategy template integrity ve non-authority

## Sonuç

- Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Kod: `src/dcabot/application/strategy_template.py`
- Test: `tests/test_strategy_template.py`
- Bağımsız review: `PASS` (Turing salt-okunur Codex incelemesi, düzeltme sonrası)
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
- Bağımsız review’da public `StrategyTemplate(...)` kurucusunun duplicate
  capability’yi kabul edebildiği bulundu. Önce eklenen regresyon `6` testte
  `1` failure verdi; `__post_init__` içine fail-closed duplicate guard eklendi.
- Güncel odak `python -m unittest tests.test_strategy_template`: `6/6 PASS`.
- İlgili projection kümesi `python -m unittest tests.test_strategy_template tests.test_rebalance_triggers`: `14/14 PASS`.
- Bağımsız canonical/hash/non-authority oracle: mapping/capability sırası,
  snapshot hash, direct-constructor duplicate guard, forbidden alanlar,
  float/NaN/Infinity reddi ve immutability `PASS`.
- Turing salt-okunur Codex review düzeltme sonrası: `PASS`; kritik P1/P2
  bulgu yok.
- `python -m compileall -q src`: `PASS`; `git diff --check`: `PASS`.
- `tools/run_checks.py` güncel tam-suite için `FAIL`: proje `Python 3.13`
  isterken kullanılabilir bundled runtime `3.12.14`; bu nedenle güncel
  tam-suite sonucu iddia edilmiyor.
- Önceki tarihsel tam-suite sonucu (`286/286`) bu oturumun doğrulaması olarak kullanılmadı.

## Kanıt sınırı

Araştırma kanıtı `docs/P1_KRITIK_ARASTIRMA_FINAL/11_P1.14_REBALANCING_SIGNAL_TEMPLATES.md` template version/hash/capability ve doğrudan order authority’nin reddini destekliyor; yerel implementation’ın geçtiğini iddia etmiyor. Bu teslim yalnız artifact integrity ve non-authority kabulüdür.
