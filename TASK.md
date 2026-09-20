# Aktif iş — Faz 2.4 tamamlama: aksiyon tablosuna klavye erişimi (CODEX BRIEF — dosya sınırlı)

Bu görev Codex'e devredildi (bkz. `docs/KARARLAR.md` "Ajanlar arası işbölümü"). Sen kimsen (Codex/Luna/Muse dahil), önce AGENTS.md + STATE.md + bu dosyayı oku. Bu dosyadaki dosya listesi ve durma koşulları bağlayıcıdır. Bu, Faz 2.4'ün (bkz. git log) kendisi değil, onun bilinen bir sınırını kapatan küçük bir ek dilimdir.

## Hedef
Faz 2.4 grafikteki marker'ları klavyeyle (Tab+Enter/Space) seçilebilir yaptı ama aksiyon tablosundaki satırlar hâlâ yalnız mouse click ile seçiliyor. Şimdi satırlar da klavyeyle (Tab ile odaklanıp Enter/Space ile) seçilebilir olsun — marker'daki ile birebir aynı davranış deseni.

## İzinli dosyalar (yalnız bunlar)
- `frontend/src/DatasetCatalogPanel.tsx`
- `frontend/src/styles.css` (yalnız ekleme; var olan kuralları silme/değiştirme)
- `frontend/src/DatasetCatalogPanel.test.tsx` (YENİ dosya — henüz yok, sen oluşturacaksın; yalnız bu davranışı test et, `HistoricalChart.test.tsx`'teki desen ve import stiliyle: `@testing-library/react`, `render`/`fireEvent`/`screen`, `vitest`'ten `describe/expect/it/vi`)

## Yasak (dokunma)
- `src/` altındaki HER ŞEY (Python backend/çekirdek).
- `frontend/src/App.tsx`, `HistoricalChart.tsx`, `HistoricalChart.test.tsx`, `savedRuns.ts`, `datasetCatalog.ts`, `SavedRunsPanel.tsx`.
- `package.json`, `vite.config.*`, `tsconfig*.json` — yeni bağımlılık yok.
- `STATE.md`, `TASK.md`, `AGENTS.md`, `docs/*`, `evidence/*`.
- `ActionTable`'ın grafik/geometri ile ilgisi yok; yalnız `rowProps` fonksiyonuna ve satır `<tr>` elemanına dokun.

## Adımlar
1. `DatasetCatalogPanel.tsx`'teki `rowProps(barIndex)` fonksiyonuna ekle: `interactive` true iken `tabIndex={0}`, `role="button"`, `aria-pressed={selected}`, `aria-label` (örn. `Bar ${barIndex} aksiyonunu seç`), `onKeyDown` (Enter/Space → `onSelectBarIndex?.(barIndex)`, `event.preventDefault()`).
2. `styles.css`'e yalnız ekleme: `.historical-action-row-interactive:focus-visible` için görünür outline (projede zaten var olan `--ui-focus-ring`/`outline` deseniyle tutarlı olsun, dosyanın başındaki `:focus-visible` kurallarına bak).
3. `DatasetCatalogPanel.test.tsx` (yeni): en az 2 test — Tab+Enter satır seçimini bildirir; Tab+Space da bildirir, ilgisiz bir tuş (örn. "a") bildirmez. `ActionTable`'ı doğrudan import edip test etmek için önce onu export etmen gerekebilir (şu an dosya içinde private/unexported olabilir kontrol et) — export etmek izinli, ama başka hiçbir public API'yi değiştirme.

## Durma koşulları (bunlardan biri olursa DEVAM ETME, raporla)
- Yukarıdaki izinli dosya listesi dışında bir değişiklik gerektiğini düşünüyorsan.
- Toplam diff ~150 satırı aşıyorsa.
- `npx tsc -b` veya `npx vitest run` 2 denemeden sonra hâlâ kırmızıysa.
- `ActionTable`'ı export etmek başka bir şeyi kırıyorsa.

## Bitti sayılması için
- `cd frontend && npx tsc -b` temiz.
- `cd frontend && npx vitest run` — tüm testler (yeni dahil) PASS.
- `git status` yalnız yukarıdaki 3 dosyayı göstermeli (2 mevcut + 1 yeni).
- Son mesajında: değişen dosyalar, eklenen test sayısı, kalan/bilinen sınır (varsa) kısa özet.

## Sonrası (Codex yapmaz, Claude yapar)
Diff review, tam checker, canlı tarayıcıda klavye testi, STATE.md/TASK.md güncelleme, commit.

## Paralel iş (bilgi amaçlı, sana ait değil)
Claude bu sırada ayrı, kesişmeyen dosyalarda (`src/dcabot/domain/`, `historical_simulation.py`) Faz 2.5 (stress modeli) tasarımı üzerinde çalışıyor olabilir. Bu senin işini etkilemez, karışma.

## Değişmez sınırlar
- Credential, secret, signed request, emir, mutation ve mainnet yok.
- Bu dilim yalnız UI erişilebilirliğidir; yeni ekonomik hesap, yeni API çağrısı, yeni bağımlılık yok.
