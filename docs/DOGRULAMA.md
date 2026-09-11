# Güncel doğrulama kapsamı

Bu plan revizyonunda Python/runtime dosyaları değiştirilmedi; önceki 38 test sonucu CORE01'e aittir. Yeni planın dosya/link ve kaynak byte bütünlüğü evidence/PLAN_DEMO_FIRST içinde. UI, HTTP, importer ve public downloader henüz yoktur; P1 PASS denmez.

P1 kalite kapıları: UI form/API/çekirdek contract ve browser E2E; gerçek tarihsel dataset/schema/checksum/time-unit; look-ahead ve fill modeli; portfolio/fee/risk oracle; job/restart/restore; Windows ve erişilebilirlik. P2/P3/P4 gerçek ağ ve operasyon kanıtı ayrıca gerekir.

Aşağıdaki N00/CORE01 bölümleri önceki teslimlerin test tarihçesidir; yeni görev sırası YOL_HARITASI P serisidir.

# Doğrulama düzeni

## Güncel CORE01 kanıtı

[evidence/CORE01/SONUC.md](../evidence/CORE01/SONUC.md): matematik, config, intent/fill/final, partial, duplicate/conflict, SQLite rollback/restart, gerçek subprocess ölümü, iki writer, replay/slippage ve CLI. Test komutu değişmedi. N00 aşağıda tarihsel ilk iskelet kanıtıdır; güncel toplamın yerine geçmez.

## N00 başlangıç tarihçesi

N00: Python 3.13'te yeni kök yerleşimi, aktif Python sözdizimi, varsayılan offline config, yalnız yeni test discovery, belirgin yedek import/link sınırı, offline bootstrap ve seçilmiş kaynak hash aracı. Sonuçlar [evidence/N00/SONUC.md](../evidence/N00/SONUC.md) içindedir.

Başlangıç komutları README'dedir. `tools/run_checks.py` standart kütüphane unittest kullanır; pytest kurmak gerekmez. uv.lock bağımlılıksız yeni projeye aittir. Yeni bağımlılık/test aracı görev kapsamında eklendiğinde kilit ve kanonik kontrol komutu birlikte güncellenir.

`check_workspace.py` sadece src/tests/tools tarar; yedeğin tüm içeriğini okumaz ve tam yedek bütünlüğünü kanıtlamaz. Yedek src/docs yerleşimi görülürse PRESENT_NOT_CONTENT_VERIFIED der. Boş yedekle başlangıç kontrolü geçebilir: uygulama bağımsızlığı kasıtlıdır. Kontrol bir sandbox veya kapsamlı dinamik import analizörü değildir.

## Davranış testleri görevle birlikte gelir

| Görev | Gereken kanıt |
|---|---|
| N01 | Bağımsız Decimal/birim örnekleri ve CLI negatif girişler |
| N02–N03 | Gerçek yeni SQLite transaction, duplicate, conflict, concurrent rezerv, rollback |
| N04a–N04b | Fake port, crash noktaları, UNKNOWN, kapsam eksikliği ve recovery |
| N05–N07 | Elle/rasyonel oracle, kısmi fill/çıkış, ücret/mark, DD ve bracket sınırları |
| N08 | Subprocess restart/sahiplik; desteklenen işletim sisteminde gerçek test |
| N09–N11 | Güncel ürün contract'ı, redakte gerçek fixture, açık yetkili testnet senaryoları |
| N13 | Veri/config/kod hash'i, aynı girdiden aynı sonuç ve açık dolum modeli |

Bir testi yanlış uygulamanın çıktısına bakarak yazıp doğru diye onaylama. Finansal hesabın beklenen sonucu formülden bağımsız türetilir. Property testleri ancak korunan invariant ve sınırları tanımlıysa yararlıdır; salt test sayısını artırmak hedef değildir.

## Kanıt kaydı

Her görev evidence/<ID>/ altında kısa sonuç bırakır: tarih, commit/diff, Python ve OS, gerçek komut/cwd/exit, beklenen-gerçek, PASS/FAIL/NOT_RUN/INCONCLUSIVE, kalan sınır ve bağımsız review durumu. Başarısız çıktıyı silip yalnız yeşil özeti saklama. Büyük veya tekrarlı raporları günlük bağlama yükleme.

## Önceki inceleme

[Arşiv KANIT](archive/onceki-inceleme/KANIT.md) eski GitHub commit'ine aittir. Oradaki Python 3.12 probe, 13 matematik vektörü ve çalıştırılmayan tam pytest bilgisi yeni kökün çalıştırma sonucu değildir. Kullanıcının yerel yedeğinin aynı commit olduğu varsayılmaz. Arşiv probe scriptleri yeniden kullanım kaynağıdır; YEDEK_ESKI_PROJE içinde kod veya test çalıştırma talimatı sayılmaz.

DCA, kalıcılık, live daemon, gerçek venue/testnet/mainnet davranışı N00'da NOT_IMPLEMENTED/NOT_RUN. N00 yeşil sonucu finansal doğruluk veya işlem güvenliği onayı değildir.
