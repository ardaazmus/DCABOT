# P1.12.f.h.an — Offline CORE01 FILL reducer projection

**Tarih:** 2026-09-17  
**Durum:** `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`  
**Legacy migration/publish:** `NOT_APPLICABLE`

## Uygulanan minimum dikey dilim

- h.am admission’ından gelen immutable CORE01 `FILL` tuple’ı yalnız kopyalanan
  CORE01 `State` üzerinde reducer’a veriliyor.
- Reducer’ın kabul ettiği exact fill sonucu; position quantity, entry notional,
  fee ve order filled/notional alanlarında projection olarak doğrulanıyor.
- Girdi state değişmiyor; projection durable Store’a, journal’a, posting’e veya
  venue transport’a yazılmıyor.
- `BLOCKED` admission hiçbir reducer çağrısı yapmadan `BLOCKED` projection
  dönüyor. Eksik/tekrarlı/değiştirilmiş tuple fail-closed reddediliyor.
- Reducer’ın terminal/UNKNOWN, overfill, off-grid veya scope hataları güvenli
  biçimde `BLOCKED` sonucuna çevriliyor; ham hata veya ekonomik varsayım
  dışarı taşınmıyor.

## Kanıt

- CORE mapping/projection odak testleri: `12/12 PASS`.
- İlişkili CORE/Store regresyon kümesi: `50/50 PASS`.
- Tam proje: `tools/run_checks.py` — `591/591 PASS`.
- `compileall`: `PASS`.
- Workspace: `PASS`, `233` aktif Python dosyası; backup layout
  `EMPTY_OR_NOT_PLACED`.
- `git diff --check`: whitespace hatası yok; yalnız mevcut LF/CRLF dönüşüm
  uyarıları görüldü.
- Canlı Binance emri, mutation, mainnet, secret, durable Store veya venue
  transport çalıştırılmadı.

## Karar

CORE01 economic `FILL` reducer geçişi artık yalnız h.am tarafından kabul
edilmiş tuple ile offline kopya state üzerinde doğrulanabiliyor. Bu hâlâ
durable economic binding değildir; persistence, idempotency/replay ve posting
atomicity sonraki ayrı kanıt kapılarıdır.

## Sıradaki tek iş

`P1.12.f.h.ao` — offline reducer projection’ının Futures DCA economic posting
ve release bağlamıyla aynı kimlik/quantity/fee sınırında salt-okunur replay
kararına bağlanması; durable Store mutation hâlâ açılmayacak.
