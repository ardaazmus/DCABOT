# Durum — 2026-09-20

Aktif faz: Faz 2.4 tamamen kapandı (marker + tablo klavye erişimi). Faz 2.1-2.4 kapandı. Dal: codex/latest-state-2026-09-20.
Doğrulanan: tam checker 879/879 PASS (0 skip); frontend tsc -b temiz, vitest 22/22 PASS.
Eksenler: implementation=IN_PROGRESS · verification=PASS · evidence_scope=LOCAL_INTEGRATION · review=NOT_RUN · deployment=NOT_DEPLOYED

## Faz 2.4 tamamlama — aksiyon tablosuna klavye erişimi (bu oturum, Codex uyguladı, Claude doğruladı+düzeltti)
- **Uygulayan:** Codex/Muse, TASK.md brief'i ile, yalnız izinli 3 dosyaya dokunarak (`DatasetCatalogPanel.tsx`, `styles.css`, yeni `DatasetCatalogPanel.test.tsx`). Diff ~76 satır.
- **Davranış:** Aksiyon tablosu satırları artık Tab+Enter/Space ile de seçilebilir (`role="button"`, `aria-pressed`, marker'daki desenle birebir). Önceki "yalnız mouse" sınırı kapandı.
- **Claude'un düzeltmesi:** Codex kendi raporunda dürüstçe belirtti — fixedSlice tablosundaki satır içi öğelerde (Kopyala butonu, detay) Enter/Space basmak satır seçimini de tetikliyordu (event bubbling). Claude `onRowKeyDown`'a `event.target !== event.currentTarget` koruması ekledi; artık yalnız satırın kendisine odaklanınca tetikleniyor.
- **Claude'un doğrulaması (bağımsız):** diff satır satır incelendi; `npx tsc -b` temiz, `npx vitest run` 22/22 PASS tekrar çalıştırıldı; tam Python checker 879/879 PASS; **canlı tarayıcıda gerçek keyboard event** (`KeyboardEvent('keydown', key:'Enter')`) tablo satırına dispatch edildi — hem satır hem eşleşen grafik marker'ı aynı anda `aria-pressed=true` oldu.
- **Yan düzeltme:** Bir önceki turda SHA256SUMS.txt, STATE.md/TASK.md stage edilmeden önce üretilmişti (sıra hatası) — manifest o ikisi için eski hash taşıyordu, checker'ı FAIL ediyordu. Bu turda düzeltildi (stage → generate sırası).

## Ajanlar arası işbölümü — ikinci uygulama sonucu
İki Codex devri de temiz: dosya allowlist'i aşılmadı, STATE/TASK/docs'a dokunulmadı. İkinci devirde Codex kendi bulduğu bir davranış kusurunu (event bubbling) düzeltmek yerine dürüstçe raporladı — brief'in "durma koşulu" ruhuna doğru uydu. Claude bunu küçük bir düzeltmeyle kapattı. Yöntem iki denemede de doğrulandı.

## Faz 2.1-2.3 özeti (önceki dilimler — ayrıntı git geçmişinde)
Sıralı deal restart + deal kimliği, Faz 2.2 ekonomik metrik seti, Faz 2.3 reproduce+compare. Hepsi canlı doğrulandı. Proje temizliği: 29 araştırma dosyası arşivlendi, `.cluster/` silindi.

## Kodda mevcut
- Yerel arayüz (FastAPI 127.0.0.1:8000 + React/Vite 5173): veri seti kaydı, public indirme, kalite raporu, OHLC grafik (etkileşimli marker, klavye dahil), doğrulama, sıralı deal + Faz 2.2 metrikleri destekli simülasyon, SQLite kayıt/listesi, reproduce doğrulama, iki-run karşılaştırma.
- CLI tools/bot.py: demo, init/replay/status/audit, preview.
- Çekirdek: exact Decimal/Fraction ladder, net TP, drawdown; idempotent SQLite kayıtları.
- P2 salt-okunur Binance testnet sınırı: public, account, user-stream adaptörleri.

## Bilinen sınırlar
- Signed REST/WS emir, mutation ve mainnet: NO-GO. Gerçek reconnect worker ve REST catch-up yok.
- Simülasyon: OHLC intrabar sırası INDETERMINATE; gerçek likidite modeli yok.
- API tek worker'a bağlı. Python 3.13 zorunlu; uv sync --frozen.

## Kararlar (2026-09-20, Claude tarafından alındı — bkz. `docs/KARARLAR.md`)
Arda çalışma kuralını netleştirdi: ürün/teknik kararları Claude alır, gerekçesiyle işaretler, açık soru olarak geri atmaz (credential/gerçek emir/mainnet hariç). Sıralı deal persistence, Faz 2 dondurma listesi onaylandı; testnet mutation gate ertelendi. Claude/Codex işbölümü kuralı iki dilimde de doğrulandı.

## Sıradaki adım
Faz 2.4 tamamen kapandı. Sırada: **Faz 2.5 — Stress modeli** (docs/YOL_HARITASI.md). Kritik/finansal olduğu için Claude yapacak (Codex'e verilmedi); tasarım önce Arda'ya sunulacak, körlemesine kod yazılmayacak.
