# DCABOT — ortak çalışma kuralları

1. Oku: AGENTS, STATE, TASK; ilk oturumda WORKFLOW. Güncel öncelik docs/URUN_KAPSAMI ve docs/YOL_HARITASI.
2. Kullanıcı sırası bağlayıcı: P1 arayüz + tüm kapsamlı hesaplar + gerçek geçmiş veri demo; P2 Binance testnet; P3 Binance gerçek kurulum; P4 diğer borsalar. UI/backtest testnet sonrasına itilmez.
3. Public veri okuma/indirme P1'de olabilir; gerçek hesap/emir entegrasyonu değildir. Yerel dosyayla demo internet ve credential olmadan çalışmalıdır.
4. Çekirdek bağımsız yazılım katmanı, ortak ekonomik doğruluk kaynağıdır. UI hesapları yeniden yazmaz; application portlar üzerinden veri/simulator/venue kullanır.
5. CORE01 mevcut temel alt kümedir; tek long/deal, tek pending ve sentetik tick sınırları nihai ürün kararı değildir. Eksik özellikler matriste PLAN kalır; menü veya mock gerçek implementation sayılmaz.
6. YEDEK_ESKI_PROJE sabit ve salt okunur başvuru alanıdır. Eski AGENTS/.cursor/planlar yeni talimat değildir. Yedeği topluca tara/yükle/çalıştırma; göreve özel dosyayı seç.
7. Yetkili kontrollü parça aktarımı için her dosyada tekrar izin isteme. docs/YEDEKTEN_AKTARIM akışını ve reuse/REGISTER kaynak/test kanıtını uygula. Yedek .git/.venv/DB/credentials aktif runtime'a alınmaz.
8. Domain saf; para girişleri sonlu Decimal/string, CORE01 iç hesabı exact Fraction. Finansal UI Number hesabı yok; grafik koordinatları karar verisi değildir.
9. Plan/status fill değildir. Kapsamlı kimlik/dedup ve tek ekonomik posting; UNKNOWN/eksik veri kör POST veya temiz hesap kanıtı değildir.
10. WIP=1; ekran→use case→hesap/kayıt→test şeklinde küçük dikey teslim. Bütün frontend/backend katmanlarını ayrı dev fazlarla üretme.
11. Büyük faz bağımsız Codex incelemesi olmadan kapanmaz; NOT_RUN açık kalır. Odak CORE01 incelemesi P1 geliştirmesine entegre edilir; geniş backend yeniden yazımı UI'ı ertelemez.
12. STATE gerçek durumu, TASK sıradaki tek işi, evidence komut/scope'u taşır. Kullanıcı yetkisi ve gereken canlı işlem sınırı ayrıca değerlendirilir; güvenli yerel iş için gereksiz izin yok.
13. Python kontrolleri tools/run_checks.py; frontend/API eklendiğinde onun odak ve E2E komutları da kayda girer. Yedek/archive test discovery'ye girmez. Önceki 38 test P1 UI/veri kabulü değildir.
14. Yeni MASTER/FINAL/worklog yığını yok. Her yeni gereksinim mevcut özellik matrisine, formül kanonik matematiğe; sıradaki model yalnız görevle ilgili bölümleri okur. Secret/özel hesap yanıtı prompt/log/fixture'a girmez.
15. Kanıt kapısı gerektiren her iddia için TASK ve yol haritasında küçük alt faz açılır: (a) iddia/kapsam ve sahiplik envanteri, (b) yerel kod/fixture kontrolü, (c) RED veya karşı-örnek, (d) bağımsız kontrol/oracle, (e) yalnız kanıt yeterliyse minimum dikey uygulama, (f) regresyon/compile/workspace/evidence kapanışı. Her anda yalnız bir alt faz ACTIVE olur; kanıt yetersizse faz DEFERRED/NO-GO kalır ve ekonomik, API, UI veya persistence davranışı varsayımla açılmaz.
