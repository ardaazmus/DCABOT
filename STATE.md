# DCABOT Durum — 2026-09-20

Aktif faz: Faz 0 — Temizlik ve kural reformu.

Son doğrulanan kaynak durumu: `codex/latest-state-2026-09-20`, commit
`f8d4455`; önceki tam yerel checker `865/865 PASS`. Faz 0.1 geri dönüş tag’i
GitHub’da: `pre-cleanup-2026-09-20`.

Eksenler: implementation=LOCAL_GREENFIELD; verification=LOCAL_PASS;
evidence_scope=LOCAL_INTEGRATION; review=PENDING; deployment=NOT_RELEASED.

## Çalışan

- P1 offline historical veri seçimi, kalite, simülasyon ve immutable kayıt
  akışları yerel olarak çalışır.
- P2.04 için offline order-list/reconciliation journal sözleşmeleri fail-closed
  testlerle korunur.
- Son checkout snapshot’ı GitHub’da ayrı `codex/latest-state-2026-09-20`
  dalında incelenebilir.
- Eski ayrıntılı durum ve görev tarihçesi silinmedi; `docs/archive/history/`
  altında korunuyor.

## Bilinen sınırlar

- Gerçek reconnect worker, REST catch-up, venue authority ve gerçek testnet
  mutation açılmadı; canlı emir ve mainnet kesinlikle kapalıdır.
- P1 uçtan uca demo kapanışı ve bağımsız inceleme tamamlanmış sayılmaz.
- P1.12/P1.13 Futures DCA/Grid sözleşmeleri canlı emir yetkisi değildir.
- Yerel çalışma alanında üretilmiş `.freebuff/` ve `src/dcabot.egg-info/`
  dosyaları Git commit’ine alınmamıştır.

## Son adım ve sıradaki adım

- Faz 0.1 tamamlandı: `pre-cleanup-2026-09-20` tag’i remote’a gönderildi.
- Faz 0.2 tamamlandı: eski `STATE.md` ve `TASK.md` arşive taşındı.
- Sıradaki iş Faz 0.3: `AGENTS.md` güvenlik çizgileri, çalışma biçimi ve
  durma kurallarıyla kısa kanonik metne dönüştürülecek.

## Açık kararlar

- `engine.py` tek-deal/çoklu-deal davranışı ürün kararı gerektirir; varsayım
  yapılmayacak.
- Gerçek testnet mutation ve mainnet için ayrıca açık kullanıcı onayı gerekir.
