# Karar defteri — DEMO_FIRST_1

Kullanıcının son ürün sırası önceki N serisi önerilerini değiştirir. Bu karar kaynak kodu veya eski yedeği değersiz kılmaz.

| ID | Karar | Önceki karara etkisi |
|---|---|---|
| ADR01 | Yeni kök + sabit yedek + kontrollü parça aktarımı | Korunur |
| ADR02 | P1 tam UI/demo; P2 Binance testnet; P3 Binance gerçek; P4 diğerleri | UI=N12 ve backtest=N13 sırası yürürlükten kalkar |
| ADR03 | Çekirdek ortak katman; demo/live/arayüz ekonomik motoru kopyalamaz | Korunur; ayrı microservice zorunlu değil |
| ADR04 | Tek long/tek deal sınırı CORE01 implementation sınırıdır | Nihai ürünü daraltan kapsam kararı kaldırılır; P1 özellik matrisi belirleyici |
| ADR05 | Gerçek geçmiş veri ilk üründe zorunlu; public ağ veri erişimi erken olabilir | Testnet bekleme koşulu kaldırılır |
| ADR06 | UI basit/uzman, tam kontrol ve analiz; salt read-only ekranla sınırlı değil | İlk ürün fonksiyonel çalışma alanıdır |
| ADR07 | Python çekirdek + FastAPI API + React/TypeScript UI hedefi | Minimal dependency/sürüm kilidi ilgili görevde eklenir |
| ADR08 | Mevcut exact hesap/Decimal sınır, dedup, UNKNOWN ve atomik journal | Korunur; yeni ürün modelleri ayrı testlerle genişler |
| ADR09 | SQLite tek makine başlangıcı; job/projection/schema planlı büyüme | Büyük tarihsel veri için ölçülen performans kapısı gerekir |
| ADR10 | Büyük faz bağımsız Codex review; odak review dikey UI işlerine eşlik eder | REVIEW_CORE01 geniş backend işi için UI'ı bekleten sıra kapısı değildir |
| ADR11 | Aktif kural AGENTS/STATE/TASK; tek özellik matrisi ve kanonik docs | Korunur; eski N/D görevleri aktif talimat sayılmaz |
| ADR12 | Veri modu ile execution modu ayrıdır; riskli mod yalnız açık yetki | Public veri bağlantısı canlı emir yetkisi açmaz |

Tam rakip eşdeğerliği, kâr üstünlüğü veya tamamlanmış UI bu belgeyle ilan edilmez. Kullanıcı hedefi kabul edilen bir ürün kapsamıdır; her gereksinim implementation/test kanıtıyla kapanır. Dış platforma bağımlı özellikler ayrıca görünürdür.

## 2026-09-20 — CORE01 tek-deal sınırı
- Karar: `State` tek-deal değişmezi ve “One base order per deal” kuralı çekirdekte kalır; nihai ürün kapsamını tek deal ile sınırlamaz.
- Gerekçe: `engine.py:292` BASE kolu yalnız taze, emirsiz `State` için geçerlidir; terminal emirler temizlenmez.
- Sonuç: deal bitince `global_new_risk_gate_open` kapanır; çekirdek aynı state içinde ikinci deal başlatmaz.
- Sınır: Çoklu deal üst katmanda sıralı deal olarak, yeni `State` ve yeni `deal_id` ile ele alınacaktır.
- Karar notu: Bu oturumda yalnız belgeleme yapıldı; `engine.py` değiştirilmedi.
