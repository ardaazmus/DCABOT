# Faz 13 kanıt — SONUC.md (TradingView webhook, 2026-09-21)

## 13.1 static-token endpoint
`POST /api/signals/webhook/tradingview`: body-embedded secret, sabit-süreli
karşılaştırma, env yoksa 409 / uyuşmazsa 401, sır asla loglanmaz/echo'lanmaz.
Zaman µs int veya UTC ISO-8601.

## 13.2 durable dedup
SQLite `webhook_intakes` (UNIQUE dedup key, WAL+FULL): aynı alert aynı
signal_id → DUPLICATE, orijinal satır değişmez. strategy_order_id aynı bardaki
alertleri ayırır; fiyat key dışında, hash içindedir.

## 13.3 fast-ACK + ayrı bind
Kabul kaydı → 200 (ACCEPTED/DUPLICATE); bağlama ayrı
`POST /api/signals/webhook/{id}/bind` adımı (depolanan intake + açık boyut).
Yeniden bind idempotent (deterministik aday).

## 13.4 internal HMAC intake
`POST /api/signals/intake`: `verify_signal_signature` relay anahtarlarıyla
(env JSON, fail-closed boş). Kaynak `internal-relay` → TV akışıyla key
çakışması yok; aynı store + bind hattı.

## 13.5 indikatörler
Pine-parity DEFERRED (ücretli API + ürün kararı). Yerine exact SMA/EMA/kesişim
(DCABOT-native, Pine iddiası yok) + `/api/signals/indicators/cross` endpoint'i.

- Tam checker 1414/1414 PASS (F13 payı +48); tsc temiz; vitest 171/171.
- `python tools/phase_gate.py F13` → GATE PASS.
