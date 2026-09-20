# Aktif iş — Faz 2.4: Etkileşimli marker (CODEX BRIEF — dosya sınırlı)

Bu görev Codex'e devredildi (bkz. `docs/KARARLAR.md` "Ajanlar arası işbölümü"). Sen kimsen (Codex/Luna dahil), önce AGENTS.md + STATE.md + bu dosyayı oku. Bu dosyadaki dosya listesi ve durma koşulları bağlayıcıdır.

## Hedef
Grafikteki bir aksiyon marker'ına tıklayınca/Enter'layınca "AKSİYON GEÇMİŞİ" tablosundaki aynı `bar_index`'e sahip satır görsel olarak vurgulanır ve görünüme kaydırılır. Tablo satırına tıklayınca da grafikteki ilgili marker vurgulanır (iki yönlü). Yeni ekonomik hesap YOK — yalnız zaten var olan `action.bar_index` join anahtarıyla UI state.

## İzinli dosyalar (yalnız bunlar)
- `frontend/src/HistoricalChart.tsx`
- `frontend/src/HistoricalChart.test.tsx`
- `frontend/src/DatasetCatalogPanel.tsx`
- `frontend/src/styles.css` (yalnız ekleme; var olan kuralları silme/değiştirme)

## Yasak (dokunma)
- `src/` altındaki HER ŞEY (Python backend/çekirdek).
- `frontend/src/App.tsx`, `savedRuns.ts`, `datasetCatalog.ts`, `SavedRunsPanel.tsx`, diğer bileşenler.
- `package.json`, `vite.config.*`, `tsconfig*.json` — yeni bağımlılık yok.
- `STATE.md`, `TASK.md`, `AGENTS.md`, `docs/*`, `evidence/*`.
- `HistoricalChart.tsx` içindeki geometri sabitleri (`PLOT_*`, `barX`, `coordinate`, `CHART_WIDTH/HEIGHT`) ve mevcut path/marker hesap mantığı — bunlar zaten doğrulanmış, DEĞİŞTİRME. Yalnız etkileşim katmanı (tıklama/klavye/vurgu) ekle.

## Neden bu dosyalar yeterli (context)
`DatasetCatalogPanel.tsx` (~satır 299-306) `HistoricalChart` ve `ActionTable`'ı zaten aynı ebeveynde, aynı `simulation.actions` verisiyle render ediyor — App.tsx'e hiç dokunmadan tek bir `useState<number | null>` (`selectedBarIndex`) bu dosyada yeterli. `HistoricalChart.tsx`'teki `ChartMarker.barIndex` ve `ActionTable`'daki `action.bar_index` zaten aynı join anahtarı.

## Adımlar
1. `HistoricalChart`'a iki opsiyonel prop ekle: `selectedBarIndex: number | null`, `onSelectBarIndex: (barIndex: number) => void`.
2. Her marker `<circle>`'ı gerçekten etkileşimli yap: `role="button"`, `tabIndex={0}`, `aria-label` (örn. `Bar ${barIndex} aksiyonunu seç`), `onClick`/`onKeyDown` (Enter/Space) → `onSelectBarIndex(barIndex)`. Seçili marker'a ayrı CSS class (örn. `historical-chart-marker-selected`) ekle. `boundary` (INCOMPLETE çizgisi) etkileşimli OLMASIN, o bir aksiyon değil.
3. `ActionTable`'a aynı iki prop'u ekle; her satıra `id={`historical-action-row-${action.bar_index}`}`, `onClick` ile seçim, `selectedBarIndex === action.bar_index` ise vurgu class'ı. Seçim değiştiğinde ilgili satırı `scrollIntoView({block:"nearest", behavior:"smooth"})` ile görünüme getir (yalnız tablo satırı, sayfa değil).
4. `DatasetCatalogPanel.tsx`'te `selectedBarIndex` state'ini tut, her iki `HistoricalChart`/`ActionTable` çiftine (normal + "PREFIX KANITI" varyantı) geçir. Yeni bir `simulation` sonucu geldiğinde (execution_id değiştiğinde) seçimi `null`'a sıfırla.
5. `styles.css`'e yalnız yeni class'lar için ekleme yap (marker seçili/hover durumu, tablo satır vurgusu); mevcut kuralları değiştirme.
6. `HistoricalChart.test.tsx`'e en az: marker click → `onSelectBarIndex` çağrılır; Enter tuşu aynısını yapar; `selectedBarIndex` prop'u verilen marker'a seçili class/aria-pressed uygulanır. Mevcut testleri kırma.

## Durma koşulları (bunlardan biri olursa DEVAM ETME, TASK.md'yi değiştirme, sonucu son mesajında raporla)
- Yukarıdaki izinli dosya listesi dışında bir değişiklik gerektiğini düşünüyorsan.
- `action.bar_index` ile grafikteki marker `barIndex`'i eşleştirmek için backend'den yeni bir alan gerekiyormuş gibi görünüyorsa (gerekmiyor, veri zaten var — tekrar kontrol et).
- Toplam diff ~200 satırı aşıyorsa.
- `npx tsc -b` veya `npx vitest run` 2 denemeden sonra hâlâ kırmızıysa.

## Bitti sayılması için
- `cd frontend && npx tsc -b` temiz.
- `cd frontend && npx vitest run` — tüm testler (yeni dahil) PASS.
- Python'a hiç dokunulmadı (`git status` içinde `src/`, `tests/`, `docs/`, `STATE.md`, `TASK.md` görünmemeli).
- Son mesajında: değişen dosyalar, eklenen test sayısı, kalan/bilinen sınır (varsa) kısa özet.

## Sonrası (Codex yapmaz, Claude yapar)
Diff review, tam checker (`uv run --frozen python tools/run_checks.py`), gerçek tarayıcıda uçtan uca deneme, STATE.md/TASK.md güncelleme, `docs/YOL_HARITASI.md` işaretleme.

## Değişmez sınırlar
- Credential, secret, signed request, emir, mutation ve mainnet yok.
- UNKNOWN, INDETERMINATE, eksik veri ve gap başarı kanıtı sayılmaz.
- Bu dilim yalnız UI etkileşimidir; yeni ekonomik hesap, yeni API çağrısı, yeni bağımlılık yok.
