# Aktif iş — Faz 3.6 kodu tamam; REAL_TESTNET kanıtı Arda'yı bekliyor

`can_transition` genişletmesi, `recover_after_restart` genişletmesi, `recover_stuck_attempts`, CLI'ye bağlama tamam. 4 yeni offline test, tam checker 934/934 PASS. Ayrıntı: STATE.md, docs/KARARLAR.md.

## Arda'nın yapması gereken (Claude yapamaz — gerçek süreç ölümü gerekir)
1. Kill-switch açık, normal şekilde başlat:
```powershell
$env:PYTHONPATH='src'
$env:DCABOT_TRADING_ENABLED='true'
uv run --frozen python tools/run_single_testnet_order.py testnet-readonly BTCUSDT BUY 0.0005 <guncel_fiyata_yakin_ama_uzak_bir_fiyat>
```
2. "Bu LIMIT emri GERCEKTEN testnet'e gondermek istiyor musun?" istemi çıktığında **EVET yazmadan, `Ctrl+C` ile kes.** (Bu, `prepare→persist` durumunda bir attempt bırakır — gerçek bir süreç ölümünü taklit eder.)
3. Aynı komutu tekrar çalıştır. Bu sefer "Onceki oturumdan kalan attempt kurtarildi: ... -> ..." satırını görmelisin (durum muhtemelen `UNRESOLVED` olacak, çünkü emir hiç gönderilmemişti).
4. Sonra normal şekilde devam et (EVET yaz, gönder/gör/iptal et).
5. Çıktının tamamını (credential/secret içermez) buraya yapıştır.

## Bu geldiğinde Claude'un yapacağı
- STATE.md'yi `evidence_scope=REAL_TESTNET` olarak günceller.
- Sıradaki: **Faz 3.7 — DCA botu testnet'te uçtan uca** için kapsam araştırması (Faz 3'ün son dilimi).

## Değişmez sınırlar
- Credential, secret, gerçek emir, mutation ve mainnet: Arda onayı olmadan asla.
- STATE.md/TASK.md yalnız Claude günceller.

## Kabul
- REAL_TESTNET kanıtı geldiğinde STATE.md güncellenir ve 3.7 brief'i yazılır.
