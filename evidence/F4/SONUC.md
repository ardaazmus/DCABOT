# Faz 4 kanıt — SONUC.md (canary altyapısı, canlı kapıya kadar, 2026-09-21)

## F4.1 tek-worker kilidi
OS-seviyesi exclusive kilit + startup/shutdown kancası; ikinci worker
açılmaz, kill sonrası devralma çalışır. 4/4 test + CANLI: çekişmede
B reddedildi, kill sonrası restart OK.

## F4.2 canary politikası
Saf exact değerlendirme: cap/kayıp/pencere/sıfır-duplicate/
sıfır-UNKNOWN/min-işlem. Dosya kill-switch (bozuk=engaged).
13/13 test (sınır değer + fail-closed dahil).

## F4.3 canlı kapı
Onay artefaktı + switch + politika üçlüsü; onaysız her durumda
`LiveTradingBlocked`. 3/3 test. Mainnet gönderen kod yok.

## F4.4 paketleme
`tools/run_api.py`: ön-kontrol + localhost + tek worker sabit;
`--workers` bayrağı yok. 4/4 test + CANLI launcher OK. README
tek giriş noktasına çevrildi.

## Canary taslağı
`config/canary.json` DRAFT değerlerle gemide, kapalılık testle
kilitli. Sayısal değerler + onay formatı Arda kararı (KARARLAR'da
soru açık). Emir gönderilmedi; mainnet kesin NO-GO.

- Tam checker 1276/1276 PASS; tsc temiz; vitest 102/102 PASS.
- `python tools/phase_gate.py F4` → GATE PASS.
