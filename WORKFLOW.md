# Çalışma düzeni ve bağlam koruması

## Kullanıcının bağlayıcı ürün sırası

P1 UI + geçmiş veri ile tam demo, P2 Binance testnet, P3 gerçek Binance kurulum, P4 diğer venue'ler. Public veri okuması P1'de olabilir. Günlük görevler docs/YOL_HARITASI P serisinden seçilir; eski N/D kodları aktif sıra değildir. Özellik kapsamı tek OZELLIK_MATRISI belgesindedir.

Her yeni özellik mümkün olan en küçük ekran→use case→hesap/kayıt→test dilimiyle gelişir. UI'ı backend bitene kadar erteleme; ekranı da sahte veriyle bitmiş sayma. Büyük faz review kuralı korunur; odak inceleme mevcut dilime eşlik eder.

## Yöntem: tek iş, küçük dikey davranış

Dikey dilim bir dosya veya tek fonksiyon demek değildir. Bir kullanıcı/operasyon davranışının girdiden kalıcı sonuca, hata ve yeniden başlatmaya kadar en küçük anlamlı parçasıdır. Örneğin “eksik sorgu sonucunda tekrar başlamayı engelle”; yalnız enum oluşturmak veya yalnız tablo açmak yeterli teslim değildir.

Bir dilimi tercihen tek oturumda bitir; süre tahmini garanti değildir. 3–7 dosya bir başlangıç hedefidir, sabit sınır değildir. Sözleşme, migration veya ekonomik transaction bütünlüğü daha çok dosya istiyorsa bölme gerekçesini değerlendir. İlişkisiz refactor ayrı iş olur. Tüm katmanları tek fazda bitiren yatay plan yoktur.

## Oturum döngüsü

1. Yeni kökte Git varsa `git status --short` ve mevcut commit'i kontrol et; yoksa bunu devirde belirt. Kullanıcı değişikliklerine dokunma. Yedekte Git komutu çalıştırma.
2. `AGENTS.md`, `STATE.md`, `TASK.md`; ilk kullanımda bu dosya. Aktif görev yoksa yol haritasından sıradaki kapısı açık tek işi seç.
3. Önce yeni src/tests içinde `rg` ile görev sembollerini ve çağıranları bul. Yedeğe yalnız docs/YEDEKTEN_AKTARIM.md akışıyla, görevde seçilen dosya için gir. TASK'a gereken gerçek yolları yaz. Dosya bulunmazsa tahmin etme.
4. Davranışın yanlışlığını gösteren bağımsız örneği ve doğru sonucu belirle. Finansal hesapta elle/rasyonel hesaplanan sonuç kullan.
5. Hata düzeltmesinde önce başarısız davranış testi, sonra minimal uygulama. Dış ağ ve clock yerine tipli girdiler/fake port kullan.
6. Odak testleri çalıştır; ilgili katmanlarda lint/type/transaction testini uygula. Çıkış kodunu, kapsamı ve eksikleri kaydet.
7. Diff'i görev dışı değişiklik, tersine dönük uyum, sayı/kimlik kaybı ve recovery etkisi için incele. Sadece test sayısını ölçme.
8. Kabul koşullarını tek tek kapat. Durumu STATE'te güncelle, tamamlanan görev ve kısa kanıtı `evidence/<task-id>/` altında sakla. TASK'ı sıradaki tek iş için değiştir.

## Çoklu yapay zekâ düzeni

Varsayılan WIP=1: aynı anda yalnız bir uygulayıcı. Planlayıcı/uygulayıcı/reviewer ayrı sorumluluklardır; aynı anda üç ajan çalıştırma zorunluluğu değildir. Her IDE için farklı plan veya kural üretme. CLAUDE/GEMINI/OPENCODE dosyaları yalnız ortak dosyalara yönlendirsin.

Model değişiminde önceki sohbet yerine taban commit, diff, TASK, komut çıktısı ve kalan tek iş devredilir. Yeni model başta çalışma ağacının devirle eşleştiğini kontrol eder. Kullanıcı paralel çalışma isterse ayrı dal/worktree ve çakışmayan dosya sahipliği gerekir; tek entegratör sırayla birleştirir. İki model aynı working tree'ye eşzamanlı yazmaz.

Önceki çalışma düzenindeki büyük faz Codex incelemesi korunur; yeni yol haritasında faz grupları belirtilmiştir. Küçük dilim için uygulayıcı öz kontrol yapar; faz sonunda başka oturumda Codex diff'i ve kritik testleri bağımsız değerlendirir. İnceleme yapılmadıysa `review=NOT_RUN`; “bağımsız doğrulandı” yazılmaz. Yetki ve bu kalite kapısı farklı şeylerdir.

## Bağlam bütçesi

| Katman | İçerik | Başlangıç hedefi |
|---|---|---|
| Sabit | AGENTS + STATE + TASK | Yaklaşık 2.000 token altında |
| Görev | İlgili spec bölümü, kod, doğrudan test | Gerektiği kadar; ilk hedef 6–12 bin token |
| Genişletme | Çağıranlar, transaction, schema, invariant | Kanıt açığına göre |
| Arşiv | Eski master plan/araştırma/sohbet | Varsayılan yüklenmez |

Bunlar model sınırı veya sektör standardı değil, ölçülebilir yerel çalışma hedefidir. Karakter/4 gerçek token sayısı değildir. Güvenlik/para/kurtarma etkisinde bütçe büyür. Eski hatayı cache için koruma; model cache'i doğruluk güvencesi sayma.

Context dolmaya yaklaşınca yeni işe başlama. Mevcut diff'i tutarlı duruma getir; henüz test edilmediyse açık yaz. Devirde tam sohbet dökümü yerine dosya ve sembol adresi ver. Sonraki oturum aynı geniş araştırmayı tekrar okumaz.

## Doküman büyümesini durdurma

- Yeni özellik için yeni “MASTER”, “FINAL”, “V4 research” belgesi yok. Mevcut kanonik bölüm güncellenir.
- Aynı bilgi iki belgede tam metin tutulmaz. Test sonucu kanıtta, güncel durum STATE'te, formül MATEMATIK'te.
- Yeni araştırma yalnız somut UNKNOWN kapatıyorsa yapılır. Sonuç: karar + kısa gerekçe + kaynak + kabul testi; uzun transkript arşivde kalır.
- Görev kartı tercihen 80 satır, STATE 40 satır, AGENTS 80 satır altında. Uzunluk kapısı içerik doğruluğunun yerine geçmez.
- Tamamlanan görevler runtime başlangıç bağlamına eklenmez. Git geçmişi aynı belgenin yüzlerce kopyasının yerine kullanılır.
- Otomatik dosya envanteri/şema raporu gerekiyorsa üretilir; elle eşzamanlı ikinci harita tutulmaz.

## Durum ayrı eksenlerdir

`implementation = NOT_STARTED | IN_PROGRESS | IMPLEMENTED`

`verification = NOT_RUN | PASS | FAIL | INCONCLUSIVE`

`evidence_scope = UNIT | LOCAL_INTEGRATION | REAL_TESTNET | CANARY`

`review = NOT_RUN | CHANGES_REQUESTED | APPROVED`

`deployment = NOT_DEPLOYED | TESTNET | MAINNET`

Yerel PASS, REAL_TESTNET veya MAINNET yapmaz. Faz ancak kendisine gerekli eksenler tamamlanınca kapanır. Doküman düzenlemesinde gereksiz ürün testleri yazılmaz; bağlantı/karar tutarlılığı kontrol edilir.

## Ölçüm

Her 5 dilimde bir: ilk incelemede kabul, geri dönen iş sayısı, çözülmemiş kritik bulgu, görev başına context/araç turu ve tekrar okunan belge sayısı. Gerçek token/metrik yoksa UNKNOWN. Amaç en kısa prompt değil, doğru tamamlanan davranış başına az tekrar iştir.
