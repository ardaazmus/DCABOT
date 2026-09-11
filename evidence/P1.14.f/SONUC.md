# P1.14.f — Template activation ve capability gate

## Sonuç

- Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Kod: `src/dcabot/application/template_activation_gate.py`
- Test: `tests/test_template_activation_gate.py`
- Bağımsız review: `NOT_RUN`
- Production readiness: `NO`
- Sonraki tek iş: `P1.15.a` hedge/cross/two-leg kapsam karar kapısı

Bu mikro-fazda strategy template’in activation kararı, declared capability allowlist’i ve açık approval durumu ayrı bir application gate olarak modellenmiştir. Gate template’i aktive etmez; candidate, order, reserve veya fill üretmez.

## Uygulanan sözleşme

- Yalnız desteklenen capability identifier’ları kabul edilir; duplicate allowlist veya duplicate template capability fail-closed reddedilir.
- `PENDING` approval ve desteklenen capability’ler `AWAITING_APPROVAL` döner.
- `APPROVED` approval ve desteklenen capability’ler `READY_FOR_ACTIVATION` döner.
- Eksik capability `CAPABILITY_UNSUPPORTED` döner; approval bunu bypass edemez.
- Approval boolean değil, açık `PENDING`/`APPROVED` string durumudur.
- Template payload’ı mutate edilmez; gerçek activation transition, profile binding ve ekonomik authority bu fazın dışındadır.

## Bilinçli kapsam dışı

Actual activation transition, user/system authorization, selected-profile parameter validation, webhook auth, order/reserve/fill binding, persistence, API ve UI eklenmedi. Gate sonucu tek başına işlem yetkisi değildir.

## Kontroller

- Önce test RED: yeni test dosyası eksik `template_activation_gate` modülü nedeniyle beklenen import error verdi.
- En küçük uygulama sonrası `uv run --frozen python tools/run_checks.py`: `290/290 PASS`.
- Bağımsız activation/capability control: pending, ready ve unsupported kararları `PASS`.
- `uv run --frozen python -m compileall -q src tests`: `PASS`.
- `uv run --frozen python tools/check_workspace.py`: `PASS`; `122` aktif Python dosyası.
- Live/testnet, credential ve gerçek emir yolu açılmadı.

## Kanıt sınırı

`docs/P1_KRITIK_ARASTIRMA_FINAL/11_P1.14_REBALANCING_SIGNAL_TEMPLATES.md` template’in inert configuration artifact olması ve activation’ın ayrı policy transition olarak ele alınması gerektiğini destekler. Bu teslim yalnız capability/approval gate davranışını uygular; production activation authority iddia etmez.
