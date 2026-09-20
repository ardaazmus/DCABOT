# P1.19.g — Frontend kritik akış component-test kapısı

## Sonuç

```text
PHASE = P1.19.g
GATE = COMPLETE_WITH_LIMITATION / LOCAL_PASS
TEST_RUNTIME = Vitest 3.2.4 + React Testing Library 16.3.0 + jsdom 26.1.0
TEST_FILES = 3
TESTS = 12/12 PASS
FRONTEND_BUILD = PASS
BACKEND_CONTRACT_CHANGE = NO
ECONOMIC_AUTHORITY_CHANGE = NO
LIVE_API_OR_MUTATION = NO
BROWSER_E2E = PASS
NVDA = PASS / USER_CONFIRMED
JAWS = NOT_RUN
NARRATOR = PASS / USER_CONFIRMED
WINDOWS_HCM = PASS / LOCAL_UI
PRODUCTION_READINESS = NO
```

## Kapsam

Bu alt faz, dış incelemelerdeki “frontend kritik akışların test paketi tarafından korunmadığı” iddiasını mevcut checkout üzerinde sınırlı ve tekrar çalıştırılabilir component testleriyle kontrol etti. Testler `frontend/` altında çalışır; backend ekonomik hesabını, API’yi veya canlı venue’yu taklit ederek yeni authority üretmez.

| Dosya | Kontrol |
|---|---|
| `frontend/src/datasetCatalog.test.ts` | Byte/hash sunumu ve indirme job aktiflik sözleşmesi |
| `frontend/src/HistoricalChart.test.tsx` | Idle/loading/error/ready, exact OHLC validation, marker metadata binding, indeterminate prefix boundary |
| `frontend/src/ExplanationSection.test.tsx` | Boş durum, backend severity grupları ve bounded technical context görünümü |

## Çalıştırılan kontroller

```text
npm --prefix D:\project\DCABOT\frontend run test
PASS — 3 test files, 12 tests

npm --prefix D:\project\DCABOT\frontend run build
PASS — tsc -b && vite build
```

## Kabul edilen davranışlar

- `HistoricalChart` idle durumunda DOM üretmez; loading ve error durumlarını erişilebilir `status`/`alert` olarak gösterir.
- Geçersiz veya tutarsız OHLC decimal verisi güvenli biçimde reddedilir; SVG çizilmez.
- Tamamlanmış simülasyonun dataset ID, artifact hash, bar sayısı veya action zamanı eşleşmezse marker katmanı kapatılır.
- Belirsiz `PREFIX_BOUNDARY_ONLY` sonuçta yalnız doğrulanmış boundary gösterilir; tamamlanmış fill marker’ı üretilmez.
- `ExplanationSection` backend’in verdiği açıklamaları ve bounded context’i gösterir; UI ekonomik hesap yapmaz.

## Sınırlar ve açık kapılar

Component testlerine ek olarak local Chromium/browser E2E çalıştırıldı. Canlı venue mutation veya credential kullanılmadı; JAWS, Narrator’ın sesli kullanıcı doğrulaması ve gerçek Windows High Contrast Mode production readiness’i açmaz.

Test runtime kurulumu npm tarafından `2` güvenlik uyarısıyla raporlandı; `npm audit fix --force` çalıştırılmadı. Bağımlılık güncellemesi ayrı, ölçümlü bakım kapısıdır.

2026-09-15 Browser E2E kanıtı: `http://127.0.0.1:5173/` açıldı; başlık `DCABOT — Bot stüdyosu` ve anlamlı DOM doğrulandı. Public venue snapshot `CONNECTED_READ_ONLY`, dataset `VERIFIED` yüklendi. Anchor fiyatı `100 → 110` değiştirildi ve preview `99/88` fiyatlı, toplam `297` plan olarak güncellendi. Historical profile seçildi; onay sonrası offline simülasyon `24 bar` işledi, sonuç ve backend açıklamaları görüntülendi. Browser console `error/warn` kaydı yoktu. Default desktop screenshot ve `390×844` mobil viewport screenshot alındı; mobil `scrollWidth=375`, `clientWidth=375`, yatay taşma yoktu. Browser runtime önce `.git` ACL `Access denied (5)` nedeniyle çalışmıyordu; yalnız `.git` kökünde gerekli `WRITE_DAC` izinleri verildikten sonra bağlantı kuruldu. Playwright fallback kullanılmadı.

2026-09-15 ücretsiz NVDA ön kontrolü: `nvda` süreci çalışırken local DCABOT ekranında 28 ardışık Tab durağı tarandı. Başlıklar, nav/main/header/footer landmark’ları, 6 form kontrolü, düğmeler, native disclosure özetleri, `status`/`aria-live` alanları ve iki tablo DOM/klavye katmanında görüldü; 28/28 durakta görünür `:focus-visible` doğrulandı. Kullanıcı sesli NVDA çıktısını onayladı; NVDA gate’i `PASS / USER_CONFIRMED` olarak kapatıldı.

2026-09-15 ücretsiz Windows Narrator ön kontrolü: Narrator süreci çalışırken aynı 28 duraklı local klavye/DOM akışı tarandı; 27/28 durakta görünür `:focus-visible`, 19 etkileşimli kontrol ve temiz `error/warn` konsolu görüldü. Kullanıcı Narrator sesli çıktısını onayladı; Narrator gate’i `PASS / USER_CONFIRMED` olarak kapatıldı. Teknik ölçümdeki body döngü durağı ayrıca korunmuştur.

2026-09-15 Windows High Contrast testi kullanıcı tarafından onaylandı ve gerçek Windows Ayarları ekranında çalıştırıldı. `Gece gökyüzü` teması uygulandığında gerçek ekran siyah arka plan, sarı focus/kenarlık ve mor seçim vurgusu gösterdi; DCABOT altında `forced-colors: active`, 9 başlık, 4 landmark, 21 kontrol, tablo başlıkları ve durum mesajları görüldü, `scrollWidth=clientWidth=1390` ile yatay taşma oluşmadı. Klavye akışında 28 adım tarandı; bir döngü geçişi body’ye döndüğü için 27 görünür focus gözlendi, gerçek etkileşimli duraklar görünür kaldı. Test bitiminde tema `Yok` olarak uygulanarak geri yüklendi; DCABOT son kontrolde `forced-colors: false`, yatay taşma yok ve `error/warn` konsolu boştu. `WINDOWS_HCM = PASS / LOCAL_UI`.

Kullanıcı onayı kaydı: High Contrast’ı test amacıyla açma, DCABOT ekranını kontrol etme ve test sonunda önceki ayara döndürme adımlarının tamamı onaylıdır. Bu kayıt, hedef Windows Ayarları penceresi erişilebilir olmadığından çalıştırma kanıtı değildir.
