# CORE01 — Gerçek doğrulama sonucu

Runtime: CPython 3.13.14, Linux x86_64. Tarih: 6 Eylül 2026. Ürün sürümü 0.1.0. Komut/cwd/stdout/stderr/exit: [commands.json](commands.json). Tek koşu kapsamı 38 unittest; failure/error/skip yok.

| Kanıt | Sonuç |
|---|---|
| Sayı/birim, ladder, tick, kısmi maliyet/exit, net TP, öğretici likidasyon ve DD | PASS |
| Intent/status fill ayrımı, kısmi/final coverage, UNKNOWN, safety iptali, geç fill | PASS |
| Duplicate/conflict, ham sentetik overfill karantinası, yabancı DB koruması | PASS |
| Posting hatasında rollback, tick ortasında rollback, SQLite iki writer yarışı | PASS |
| Gerçek alt süreç os._exit(17), tekrar açma ve güvenli retry | PASS |
| Exact state + per-event balanced posting restore/audit | PASS |
| Bilinen demo, gap başına tek seviye, fee/funding rebate, slippage | PASS |
| Ayrı CLI process'leriyle init/replay/repeat/status/audit | PASS |
| Mevcut DB'ye init, float/duplicate JSON/mainnet config negatif yolları | Beklenen exit 2; PASS |
| Ruff 0.12.12 E4/E7/E9/F ve format --check | PASS |
| Python sürüm/uv.lock ve yedek dışı workspace kontrolü | PASS |

## Bağımsız beklenen sonuçlar

- 100.25 × 0.04 = 4.01.
- 100 anchor, %10 sabit cumulative deviation: 90/80/70.
- 1@100 + 1@90, sonra 0.5@110: qty=1.5, cost=142.5, average=95, gross realized=7.5.
- Bu pozisyon mark100, toplam fee0.245 ve funding0.2: equity=1014.555 (başlangıç1000).
- Net TP örneği 96.15; net=1.9177. Öğretici likidasyon kökü=18000/199; borsa kökü olduğu iddia edilmez.
- 100→120→100 equity: DD=1/6.
- Demo: gross30, fee0.57, net29.43, ending equity1029.43; MDD0.03027. Aynı input tekrarında aynı state ve 16 event.
- %1 slippage demo: gross24.3, fee0.5697, equity1023.7303; slippage tekrar gider yazılmaz.

## Geliştirme sırasında görülenler

İlk test çağrısı yanlış çalışma dizininden yapıldığı için dosya bulunamadı (exit2); doğru proje kökünde tekrarlandı. Matematik testleri kod yazılmadan önce eksik module ile hata verdi, uygulama sonrası geçti. Ruff ilk kontrolde üç kullanılmayan importu kaldırdı; son check ve format kontrolü PASS. Eski N00 test kanıtı tarihsel bırakıldı, yeni sonuçlara eklenmedi.

## Sınırlar

implementation=IMPLEMENTED yalnız docs/CEKIRDEK_KULLANIM kapsamı. verification=PASS; evidence_scope=OFFLINE_UNIT_AND_LOCAL_INTEGRATION. review=NOT_RUN (bağımsız ikinci Codex oturumu yapılmadı). deployment=NOT_DEPLOYED.

Gerçek Windows/PowerShell çalıştırması, live venue/permission, outbox sender, account-wide rezerv, dış reconciliation, gerçek borsa overfill/reversal muhasebesi, venue margin/bracket, OHLC/likidite backtest'i ve mainnet NOT_IMPLEMENTED/NOT_RUN. Fonksiyonel testler testnet veya finansal performans sertifikası değildir. Tam type-check ve ileri performans/stres testleri NOT_RUN.

Kullanıcının yerel eski yedeği mevcut değildi; eski modüller kopyalanmadı veya çalıştırılmadı. Büyük fazın sonraki kalite kapısı TASK.md bağımsız incelemesidir.

## ZIP açılış kontrolü

Paket ayrı geçici dizine çıkarıldı. Eski yedek ve .venv olmadan Python3.13 ile 38 test ve demo yeniden geçti. [Çıkarılan ZIP kanıtı](extracted_zip_checks.json). Teslim SHA256SUMS.txt dosyası her pakete giren dosyanın hash'ini taşır.
