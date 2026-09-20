# P1.12.f.h.a — Ayrı ledger failure-injection kapısı

**Tarih:** 2026-09-17  
**Durum:** `LOCAL_PASS / NO-GO_CONFIRMED`

## Kanıt

`tests/test_futures_dca_atomicity_gate.py`, event journal commit’inden sonra
reservation commit’inden önce enjekte edilen bir failure ile iki ayrı SQLite
ledger’ın farklı kalabildiğini gösterir: event restart sonrası görünürken
reservation ledger’ı unchanged kalır.

Bu test bir production coordinator veya ekonomik binding üretmez. Tam tersine,
mevcut iki-store yaklaşımıyla “event kabul edildi ve rezervasyon da atomik
olarak bağlandı” iddiasının güvenli olmadığını kanıtlar. Aynı risk ters commit
sırasında da vardır; bu dilim onu varsayımla kapatmaz.

## Sınır

Base→quote commitment, fee/slippage/rounding, partial/cancel/late/UNKNOWN
release ve position/economic posting identity hâlâ çözülmemiştir. Bu nedenle
P1.12.f.h implementation ve P1.12.g lifecycle authority açılmaz.

## Test sonucu

- Odak failure-injection: `1/1 PASS`
- Production kodu ve dış dependency değişmedi.
- Son tam proje kontrolü: `525/525 PASS`.

Sıradaki tek iş, bu dört ekonomik sözleşme için bağımsız exact oracle ve tek
bounded SQLite journal tasarımının failure/restart kabulüdür.
