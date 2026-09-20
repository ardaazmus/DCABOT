# P1.14.f — Template activation ve capability gate

## Sonuç

- Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Kod: `src/dcabot/application/template_activation_gate.py`
- Test: `tests/test_template_activation_gate.py`
- Bağımsız review: `PASS` (Singer salt-okunur Codex incelemesi)
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
- Güncel odak `python -m unittest tests.test_template_activation_gate`: `4/4 PASS`.
- İlgili template/projection kümesi `python -m unittest tests.test_template_activation_gate tests.test_strategy_template`: `10/10 PASS`.
- Bağımsız template activation oracle: pending/approved/unsupported precedence,
  duplicate ve bool allowlist/approval reddi, immutable decision ve non-authority `PASS`.
- Singer salt-okunur Codex review: `PASS`; kritik P1/P2 bulgu yok.
- `python -m compileall -q src`: `PASS`; `git diff --check`: `PASS`.
- `tools/run_checks.py` güncel tam-suite için `FAIL`: proje `Python 3.13`
  isterken kullanılabilir bundled runtime `3.12.14`; bu nedenle güncel
  tam-suite sonucu iddia edilmiyor.
- Önceki tarihsel tam-suite sonucu (`290/290`) bu oturumun doğrulaması olarak kullanılmadı.
- Live/testnet, credential ve gerçek emir yolu açılmadı.

## Kanıt sınırı

`docs/P1_KRITIK_ARASTIRMA_FINAL/11_P1.14_REBALANCING_SIGNAL_TEMPLATES.md` template’in inert configuration artifact olması ve activation’ın ayrı policy transition olarak ele alınması gerektiğini destekler. Bu teslim yalnız capability/approval gate davranışını uygular; production activation authority iddia etmez.
