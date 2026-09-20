# P1.20 — Tam Demo Kabulü ve Bağımsız İnceleme Sonucu

## Karar

```text
P1.20_STATUS = COMPLETE_WITH_LIMITATION
IMPLEMENTATION_GATE = LOCAL_PASS
PRODUCTION_READINESS = NO
```

P1 demo akışı gerçek yerel frontend ve backend birlikte çalışırken uçtan uca tamamlandı:

```text
verified dataset → historical profile/config → run plan → confirmation
→ simulation → economic/result inspection → save → Saved Runs list
→ immutable read-only detail → 390px detail inspection
```

Bu kabul; mevcut P1.20 demo dilimini doğrular. Özellik matrisindeki PLAN, DEFERRED veya NO-GO maddelerini tamamlanmış ilan etmez.

## Doğrulanan çalışma alanı

- Frontend: `http://127.0.0.1:5173/`
- Backend health: `GET /api/health` → `status=ok`, `mode=offline`, `trading_enabled=false`
- Capability: `data_mode=HISTORY_LOCAL`, `execution_mode=SIMULATED`, `trading_enabled=false`
- Dataset sayısı: `1`
- Dataset: `binance-spot-klines-v1-btcusdt-1h-2025-01-01`
- Dataset durumu: `VERIFIED`
- Dataset SHA-256: `8077644eb5088200969b135d7046ba777281be303fa32aceff28fe3baeaa5873`
- Dataset boyutu: `1591` byte
- Historical profile: `historical_demo_btcusdt_1h_v1`
- Kapsam: `BTCUSDT`, `1h`, `24` kapalı bar, `USDT`
- Venue filtresi: `project_fixture`; tarihsel venue filtresi iddiası yapılmadı
- Sonuç: `COMPLETED`, `persisted=false` aşamasında gösterildi ve kullanıcı eylemiyle kaydedildi
- Kayıtlı koşu listesi: `2` kayıt; her iki kayıt da doğrulanmış görünür durumda
- Son açılan kayıt: `6dfbba98-d3bb-4e94-8987-b4dd1a08d465`

## Demo kontrol matrisi

| Kontrol | Sonuç | Kanıt |
|---|---|---|
| Sayfa kimliği ve URL | PASS | `DCABOT — Bot stüdyosu`, local URL |
| Dataset seçimi | PASS | VERIFIED dataset kartı ve seçili ayrıntı paneli |
| Preflight | PASS | BTCUSDT/1h/24 bar kapsamı ve verified artifact |
| Historical profile/config | PASS | `historical_demo_btcusdt_1h_v1`, SIMULATED, read-only |
| Run plan | PASS | Beklenen dataset ile eşleşme ve config snapshot |
| Onay adımı | PASS | “Simülasyonu başlat?” ekranı, 24 kapalı bar özeti |
| Simulation | PASS | `COMPLETED`, 24 bar işlendi |
| Economic summary | PASS | Backend değerleri doğrudan gösterildi; frontend hesaplaması yok |
| Explanation projection | PASS | 5 kart: 3 WARNING, 2 INFO; kartlar render edildi |
| Chart | PASS | 24 kapalı bar, 1 nötr action marker, READ-ONLY sınırı |
| Action history | PASS | 1 backend action snapshot satırı |
| Save | PASS | “Koşu kaydedildi” durumu ve kayıt açma bağlantısı |
| Saved Runs list | PASS | 2 doğrulanmış kayıt listelendi |
| Read-only detail | PASS | Dataset evidence, execution identity ve immutable sınır görünür |
| 390px detail | PASS | Sayfa yatay taşmadı; `scrollWidth=clientWidth=375` |
| Uygulama konsolu | PASS | Browser smoke sırasında uygulama error olayı yok |
| Güvenlik sınırı | PASS | Credential, live/testnet order, LLM ve network data akışı yok |

## Sonuç ve ekonomik sınır

Demo sonuç ekranı backend tarafından verilen değerleri gösterdi. Bu çalıştırmada UI’da görülen başlıca sonuçlar:

- `24` bar işlendi.
- `1` action kaydı gösterildi.
- Realized gross: `0`
- Fees: `0.374304`
- Realized net after all costs: `-0.374304`
- Position status: `OPEN_AT_END`
- Funding: `NOT_MODELED`
- Mark: `NOT_AVAILABLE`

Bu alanlar frontend tarafından yeniden hesaplanmadı. Theme/focus çalışması kapsamında yapılan tek uygulama değişikliği, Saved Runs görünümünün `900px` altındaki genişliklerde kart düzenine geçmesini sağlayan CSS media-query düzeltmesidir.

## Responsive bulgu ve düzeltme

İlk P1.20 kontrolünde Saved Runs görünümünde `768px` genişlikte tablo dışarı taşıyordu. Minimum düzeltme olarak ilgili responsive eşik `720px` yerine `900px` yapıldı. Son kontrolde:

| Genişlik | Sonuç |
|---:|---|
| 320px | PASS, page overflow yok |
| 390px | PASS, page overflow yok |
| 768px | PASS, kart düzeni; page overflow yok |
| 1024px | PASS, tablo iç scroll sınırlı |
| 1280px | PASS, page overflow yok |

## Çalıştırılan kontroller

- `uv ... python tools/run_checks.py` → `359/359 PASS`
- `uv ... python tools/check_workspace.py` → `PASS`
- Python 3.13 ortamında `compileall -q src tests` → `PASS`
- `frontend/npm run build` → `PASS`
- Chrome CDP fallback ile gerçek local render/interaction smoke → `PASS`

## Sınırlamalar

- NVDA ve JAWS gerçek etkileşimli oturumu çalıştırılmadı; bu nedenle tam screen-reader uyumluluğu veya WCAG uygunluk sertifikası iddia edilmez.
- Gerçek Windows High Contrast Mode oturumu çalıştırılmadı; yalnız browser forced-colors emülasyonu önceki erişilebilirlik QA kanıtında mevcut.
- Browser plugin kernel-assets yolu çalışmadığı için doğrudan kurulu Chrome CDP fallback’i kullanıldı.
- Demo `project_fixture` niteliğindeki sabit yerel artifact ile çalıştı; canlı Binance WebSocket/REST, reconnect/catch-up veya credential kullanılmadı.
- P1.20, özellik matrisindeki tüm PLAN maddelerini kapatmaz; testnet/live entegrasyonu P1 kabulünün dışındadır.

## Değişen dosya

- `frontend/src/styles.css` — Saved Runs responsive eşik düzeltmesi.
- `evidence/P1.20/SONUC.md` — Bu kabul ve kanıt raporu.

## Görsel kanıtlar

Not (2026-09-20): aşağıdaki `.cluster/` bağlantıları artık geçersiz; klasör Arda onayıyla temizlendi. Tarihsel kayıt olarak bırakıldı, tekrar üretilebilir kanıt değildir.

- [1280px tamamlanmış demo](../../.cluster/P1.20-demo/demo-1280-completed.png)
- [1280px Saved Runs listesi](../../.cluster/P1.20-demo/demo-1280-saved-runs.png)
- [1280px salt-okunur kayıt ayrıntısı](../../.cluster/P1.20-demo/demo-1280-saved-detail.png)
- [390px salt-okunur kayıt ayrıntısı](../../.cluster/P1.20-demo/demo-390-saved-detail.png)

## Nihai karar

P1.20 yerel tam demo akışı `LOCAL_PASS` olarak kapatılabilir. Üretim erişilebilirlik readiness değeri `NO` kalır; bunun nedeni demo akışının başarısız olması değil, NVDA/JAWS ve gerçek Windows High Contrast Mode doğrulamasının bu ortamda çalıştırılmamış olmasıdır.
