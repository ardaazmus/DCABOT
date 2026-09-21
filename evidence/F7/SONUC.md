# Faz 7 kanıt — SONUC.md (F17 rebalancing + F19 signal, ≤60 satır)

## F7.1 explicit-price valuation + plan kimliği (2026-09-21)
`value_holdings` (explicit conversion price, self-price yasak, eksik/fazla
fiyat fail-closed) + `build_rebalance_plan` (yalnız TRIGGERED gate, sha256
canonical plan_id, DRAFT statü — emir yetkisi yok). 10/10 yeni test.
## F7.2 signal intake (2026-09-21)
Canonical payload hash (JCS profili) + HMAC-SHA256 auth (sabit-zamanlı
karşılaştırma, hata mesajında anahtar yok) + event-time replay penceresi
(future/expired/duplicate fail-closed). 12/12 yeni test (sabit HMAC vektörlü).
## F7.3 valuation API + UI (2026-09-21)
`POST /api/rebalance/valuation` (preview deseni: validate/calculate, 422
fail-closed) + RebalancePanel (satır girişi, sonuç tablosu, salt-okunur
sınır notu) + App bağlantısı. 6/6 API + 6/6 panel testi. Canlı duman:
gerçek uvicorn'a POST → total_equity 600 exact doğrulandı.
## F7.4 execution disclosure + candidate binding + API/UI (2026-09-21)
Satır-bazında fee/rounding disclosure (kalıntı açık, skip nedenli) + rezerv
kontrolü (yetmezse BLOCKED) + deterministik aday bağlama; READY sinyal→
expiring candidate (explicit map+sizing). 5 endpoint (plan/disclose/hash/
assess/candidates) + RebalancePlanPanel/SignalPanel. 10/10 + 9/9 + 11/11
backend, 6/6 panel testi. CANLI: plan→READY(2 aday)→hash→CANDIDATE kanıtlı.
- Tam checker 1095/1095 PASS; tsc temiz; vitest 63/63 PASS.
- `python tools/phase_gate.py F7` → GATE PASS.
F17+F19 kapandı (venue order gönderimi kapsam-dışı).
Yeni (F7.4): rebalance_execution.py, signal_candidate_binding.py,
RebalancePlanPanel/SignalPanel.tsx(+test), 4 test dosyası.
Yeni (F7.1-3): rebalance_valuation.py, signal_intake.py,
RebalancePanel.tsx(+test), 3 test dosyası.
