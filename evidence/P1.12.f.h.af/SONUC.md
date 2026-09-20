# P1.12.f.h.af — Futures DCA release transition state machine

**Tarih:** 2026-09-17  
**Durum:** `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`  
**Legacy migration/publish:** `NOT_APPLICABLE`

## Uygulanan minimum dikey dilim

- Partial fill, full fill, cancel, late fill ve UNKNOWN için explicit transition
  türleri tanımlandı.
- `reserved = consumed + releasable` exact conservation zorunlu tutuldu.
- Partial/full fill consumed miktarı yalnız artar; cancel yeni fill üretemez.
- Late/UNKNOWN ekonomik miktarları değiştirmeden `QUARANTINED` durumuna taşır.
- Her yeni transition için `release_cursor = önceki + 1` ve optimistic version
  eşleşmesi zorunlu; gap, stale version ve terminal state geçişleri fail-closed.
- Aynı release identity/cursor ve aynı projection yeniden çalıştırıldığında
  `DUPLICATE`; farklı payload `CONFLICT` olur.

Bu mikro-faz saf projection’dır. Journal satırının durable update’i ve transition
history’sinin tek transaction ile persist edilmesi sonraki mikro-fazda ele
alınacaktır; mevcut projection ekonomik venue veya canlı emir otoritesi değildir.

## Kanıt

- Yeni state-machine testleri: `4/4 PASS`.
- Tam proje: `tools/run_checks.py` — `569/569 PASS`.
- `compileall`: `PASS`.
- Workspace: `PASS`, `226` aktif Python dosyası; backup layout `EMPTY_OR_NOT_PLACED`.
- Canlı Binance emri, mutation, mainnet, secret veya migration çalıştırılmadı.

## Sıradaki tek iş

`P1.12.f.h.ag` — release transition projection’ını bounded journal’da optimistic
version + release cursor ile durable ve atomic update eden persistence kapısı.
