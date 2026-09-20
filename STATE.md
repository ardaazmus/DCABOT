# Durum — 2026-09-20

Aktif faz: Faz 2.4 — etkileşimli marker, Codex tarafından uygulandı, Claude tarafından doğrulandı ve kapatıldı. Faz 2.1-2.4 kapandı. Dal: codex/latest-state-2026-09-20.
Doğrulanan: tam checker 879/879 PASS (0 skip); frontend tsc -b temiz, vitest 19/19 PASS (13 önceki + 6 yeni).
Eksenler: implementation=IN_PROGRESS · verification=PASS · evidence_scope=LOCAL_INTEGRATION · review=NOT_RUN · deployment=NOT_DEPLOYED

## Faz 2.4 — Etkileşimli marker (bu oturum, Codex uyguladı, Claude doğruladı)
- **Uygulayan:** Codex/Muse, TASK.md brief'i ile, yalnız izinli 4 dosyaya dokunarak (`HistoricalChart.tsx`, `HistoricalChart.test.tsx`, `DatasetCatalogPanel.tsx`, `styles.css`). Diff: +185/−12, ~200 satır sınırının altında.
- **Davranış:** Grafikteki aksiyon marker'ı tıklama/Enter/Space ile seçilebilir (`role="button"`, `aria-pressed`); seçim `PreflightCard`'da tek bir `selectedBarIndex` state'i üzerinden hem `HistoricalChart`'a hem `ActionTable`'a akar; tablo satırı da tıklanabilir, seçili satır `scrollIntoView` ile görünüme gelir. Yeni simülasyon (`execution_id` değişince) seçim sıfırlanır. Geometri sabitleri ve boundary (INCOMPLETE) çizgisi dokunulmadan, etkileşimsiz bırakıldı.
- **Claude'un doğrulaması (bağımsız, Codex'in raporuna güvenmeden):** `git diff` satır satır incelendi (yalnız izinli dosyalar, geometri mantığı değişmemiş); `npx tsc -b` ve `npx vitest run` (19/19) tekrar çalıştırıldı; tam Python checker 879/879 PASS (backend'e dokunulmadığı doğrulandı); **gerçek tarayıcıda canlı test**: marker tıklanınca DOM'da `aria-pressed=true` + `historical-chart-marker-selected` class'ı VE aynı anda tablo satırında `historical-action-row-selected` class'ı oluştuğu doğrudan JS ile doğrulandı (gerçek VERIFIED BTCUSDT run'ıyla).
- Bilinen sınır (Codex'in kendi notu, doğru): tablo satırları yalnız mouse click ile seçilir; klavye kullanıcıları seçimi marker üzerinden (Tab+Enter/Space) yapar.

## Ajanlar arası işbölümü — ilk uygulama sonucu
Faz 2.4, Claude/Codex işbölümü kuralının (AGENTS.md, docs/KARARLAR.md) ilk denemesiydi: dosya allowlist'li brief TASK.md'ye yazıldı, Codex yalnız izinli dosyalara dokundu, STATE/TASK/docs'a dokunmadı, durma koşullarını aşmadı. Sonuç: temiz, izole, doğrulanabilir bir diff — yöntem işe yaradı.

## Faz 2.1-2.3 özeti (önceki dilimler, uygulandı — ayrıntı git geçmişinde)
Sıralı deal restart + deal kimliği (`deal_id`/`event_sequence`), Faz 2.2 ekonomik metrik seti (action_count/average_entry_price/time_in_position_us + zaten var olan net PnL/max drawdown/fees'in persist edilmesi), Faz 2.3 reproduce (`POST /api/historical-runs/{run_id}/reproduce`) + compare (frontend, yeni endpoint gerekmedi). Hepsi canlı tarayıcıda denendi. Proje temizliği: 29 araştırma dosyası arşivlendi, `.cluster/` silindi.

## Kodda mevcut
- Yerel arayüz (FastAPI 127.0.0.1:8000 + React/Vite 5173): veri seti kaydı, public indirme, kalite raporu, OHLC grafik (**artık etkileşimli marker**), doğrulama, sıralı deal + Faz 2.2 metrikleri destekli simülasyon, SQLite kayıt/listesi, reproduce doğrulama, iki-run karşılaştırma.
- CLI tools/bot.py: demo, init/replay/status/audit, preview.
- Çekirdek: exact Decimal/Fraction ladder, net TP, drawdown; idempotent SQLite kayıtları.
- P2 salt-okunur Binance testnet sınırı: public, account, user-stream adaptörleri.

## Bilinen sınırlar
- Signed REST/WS emir, mutation ve mainnet: NO-GO. Gerçek reconnect worker ve REST catch-up yok.
- Simülasyon: OHLC intrabar sırası INDETERMINATE; gerçek likidite modeli yok.
- Marker seçimi klavyeyle yalnız grafik üzerinden yapılabilir, tablo satırından değil (kabul edilebilir sınır).
- API tek worker'a bağlı. Python 3.13 zorunlu; uv sync --frozen.

## Kararlar (2026-09-20, Claude tarafından alındı — bkz. `docs/KARARLAR.md`)
Arda çalışma kuralını netleştirdi: ürün/teknik kararları Claude alır, gerekçesiyle işaretler, açık soru olarak geri atmaz (credential/gerçek emir/mainnet hariç). Sıralı deal persistence, Faz 2 dondurma listesi onaylandı; testnet mutation gate ertelendi. Claude/Codex işbölümü kuralı kondu ve Faz 2.4'te başarıyla test edildi.

## Sıradaki adım
Faz 2.1-2.4 commit edildi (bkz. git log). İki paralel iş başladı:
1. **Codex**: Faz 2.4'ün bilinen sınırını kapatan küçük ek dilim — aksiyon tablosu satırlarına klavye erişimi (TASK.md brief'i, dosya sınırlı, kesişmiyor).
2. **Claude**: Faz 2.5 — Stress modeli (docs/YOL_HARITASI.md: "yalnız 2.1–2.4 bittikten sonra, sınırlı tek dilim") tasarımı; kritik/finansal olduğu için Codex'e verilmedi (bkz. Ajanlar arası işbölümü).
