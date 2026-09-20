# Aktif iş — Faz 3.1 kod tamam, REAL_TESTNET kanıtı Arda'yı bekliyor

`src/dcabot/application/user_stream_reconnect_worker.py` (reconnect worker) ve `tools/run_user_stream_reconnect_worker.py` (canlı çalıştırma aracı) yazıldı, offline test edildi (`tests/test_user_stream_reconnect_worker.py`, 6/6 PASS), tam checker 886/886 PASS. Ayrıntı: STATE.md, docs/KARARLAR.md ("Faz 3.1 kapsam netleştirmesi").

## Arda'nın yapması gereken (Claude yapamaz — credential + gerçek ağ gerekir)
1. `uv run --frozen python tools/configure_testnet_credential.py <credential_id>` — testnet API key/secret'ı yerel Windows Credential Manager'a kaydet (repoya girmez).
2. `$env:PYTHONPATH='src'; uv run --frozen python tools/run_user_stream_reconnect_worker.py <credential_id>` çalıştır.
3. `CONNECTED` satırını gördükten sonra ağı kes/aç.
4. Log'da `DISCONNECTED → RECONNECTING → RECONNECTED` görülmeli (gerçek `GAP` garanti değil — o an bir event kaçarsa görülür).
5. Ctrl+C, redakte log'u (credential/secret içermez) Claude'a yapıştır.

## Bu geldiğinde Claude'un yapacağı
- Log'u STATE.md'ye `evidence_scope=REAL_TESTNET` olarak işler.
- **3.2 — REST catch-up**'a geçer: gap sonrası açık emir/işlem sorgusuyla snapshot, `apply_authoritative_snapshot`'a bağlanan authoritative REST lookup. Bu, `persistence/`/`application/reconciliation.py` sınırına giren kritik bir dilim — Claude yapar, Codex'e verilmez.

## Değişmez sınırlar
- Credential, secret, signed request, gerçek emir, mutation ve mainnet: Arda onayı olmadan asla. Claude `tools/run_user_stream_reconnect_worker.py`'yi kendisi hiç çalıştırmaz.
- STATE.md/TASK.md yalnız Claude günceller.

## Kabul
- REAL_TESTNET kanıtı geldiğinde STATE.md güncellenir ve 3.2 brief'i yazılır.
- Kanıt gelmeden 3.2'ye geçilmez (roadmap: "Her dilim evidence_scope=REAL_TESTNET üretmiyorsa iş sayılmaz" — bu, 3.1'in kendisi için geçerli; 3.2 3.1'in kanıtına dayanmadan da tasarlanabilir ama commit edilmeden önce 3.1 kanıtı beklenir).
