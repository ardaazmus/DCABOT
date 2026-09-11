# Arayüz ve etkileşim sözleşmesi

Hedef: 3Commas/Pionex sınıfındaki çalışma yoğunluğunu sade bir akışta sunan özgün ürün. Bu belge uygulanacak tasarımı tarif eder; ZIP'te bitmiş frontend yoktur. Marka/logo/görseller kopyalanmaz.

## Görsel sistem

Koyu ve açık tema, nötr slate yüzeyler, mavi ana aksiyon, okunur yeşil/kırmızı sonuçlar; durum yalnız renkle anlatılmaz. 8 px aralık sistemi, 12 px kart köşesi; tutarlı font ve tablo yoğunluğu. Türkçe varsayılan; uluslararasılaştırma anahtarları, ondalık girişte yerel gösterim ile API'nin noktalı string formatı ayrı. Para değerleri tabular numeral, miktar birimi görünür.

Masaüstünde 240 px sol menü, üstte mod/veri zamanı ve arama; ana içerikte kart/tablo/çalışma alanı. 1280 px üstünde builder form + chart + economic summary düzeni; orta ekranda iki panel, mobilde sekmeli tek panel. 360 px genişlikte temel akış yatay sayfa taşması olmadan çalışır; geniş tablo kendi scroll bölgesini kullanır. Kısayollar, görünür focus, klavye ile işlem ve ekran okuyucu etiketleri hedef kabulün parçasıdır.

Basit görünüm başlangıç/averaging/çıkış/risk özetini gösterir; uzman görünüm aynı config üzerinde koşul ağacı, fill modeli, fee/bracket ve execution ayrıntısını açar. Gizlenen alanlar kaybolmaz veya sessiz default'a dönmez.

## Ekranlar ve gerçek davranış

| Ekran | İçerik ve temel aksiyon |
|---|---|
| Başlangıç | Demo ile başla, veri içe aktar, örnek veri; API anahtarı sorulmaz |
| Genel bakış | Equity/net PnL/MDD/serbest-rezerve fonlar; aktif botlar, veri kalitesi, kritik olay |
| Veri merkezi | Dosya/online kaynak, sembol/ürün/tarih, indirme ilerlemesi, gap raporu, katalog |
| Botlar | Arama/filtre/favori, toplu pause/stop, clone, archive; state/reason görünür |
| Bot stüdyosu | Basit/uzman form, interaktif ladder, chart overlay, bütçe/fee/risk önizleme |
| İşlem terminali | Manuel simulated emir, split TP, stop/trailing/breakeven; trade timeline |
| Backtest laboratuvarı | Dataset, dönem, model, parametre kıyası; progress/cancel, results/history |
| Koşu detayı | Candle/trade chart, fills, TP/SL, equity/DD, fee/funding dökümü; olaydan grafiğe geçiş |
| Portföy/risk | Çok bot/pair exposure, allocation/rebalancing, account limitleri ve stress |
| Şablonlar/sinyaller | Sürüm/diff, import/export, sinyal replay/test; tetik nedeni ve dedup |
| Olay ve bildirim | Hata/UNKNOWN/data stale; neden, etki ve uygulanabilir sonraki aksiyon |
| Bağlantılar/ayarlar | Public data ayrı; ileride testnet/live wizard, yetenek ve sağlık; tema/dil/backup |
| Yardım/asistan | Alan açıklaması, hesap formülü, örnek; isteğe bağlı doğal dil önerisi ve önizleme |

## Birincil akış: kuruluma değil sonuca götür

Demo ile başla → veri yükle veya indir → kalite özetini incele → şablon/bot ayarları → ekonomik önizleme → geçmiş dönemi çalıştır → sonucu grafik ve kayıtla incele → karşılaştır/kaydet. API credentials sadece P2/P3 bağlantı ekranında, seçili ortam için görünür.

Formda yetersiz bütçe somut gösterilir: “Plan 1.240 USDT notional kullanıyor; limit 1.000 USDT.” Veri eksikliği somut: “Bu dönemin 12 funding olayı eksik; net sonuç tamamlanamadı.” Başarı mesajı gerçek kalıcı run_id'ye bağlanır; yalnız butona basıldığı için başarılı toast yoktur.

## İşlem denetimi

Pause yeni niyet üretimini durdurur; stop-after-deal mevcut deal'i bitirir; cancel pending emirleri hedefler; close/flatten pozisyonu azaltır. Bunlar tek belirsiz “durdur” butonu altında aynı işi yapmaz. DEMO eylemleri de command_id ile kaydedilir. Aktif bot config değişikliğinde “yeni deal'lere uygula” veya açık migration/replace planı; sessizce mevcut emirlerin fiyatını değiştirme yok.

Çizgi sürüklenince form güncellenir, backend yeniden hesaplar; doğrulama bitmeden apply aktif olmaz. Unsaved state ve değişiklik diff'i görünür. HTTP yanıtları config revision taşır; yarışta eski sonuç geri yüklenmez. Tablo filtreleri/sekme/yoğunluk kullanıcı tercihi olarak saklanır, finansal config'e karışmaz.

## Üstünlük hedefleri — kendi ürün ölçütlerimiz

- Bir işlem satırından grafikte fill'e ve fee/maliyet hesabına en çok iki etkileşim.
- “Neden işlem açmadı?”: bütçe, veri, koşul veya UNKNOWN nedenini görünür ver.
- Parametre değişikliğinin notional, fee ve stres equity farkını önce/sonra göster.
- Üç koşuyu aynı veri/model altında yan yana kıyasla; uyuşmayan varsayımları gizleme.
- Replay play/pause/step/speed; geçmiş noktaya geri gitme snapshot/replay üzerinden, olay geçmişini mutasyona uğratmadan.
- Veri güven puanı yerine somut eksik/gap/varsayım listesi ve hesap kapsamı.
- Demo/testnet/live sürekli üst rozet, ayrı hesap/run alanı; renk dışı metinsel uyarı.

## UI kabulü

Loading, boş sonuç, hata, iptal, stale veri ve kısmi başarı tasarlanır. Bütün görünür P1 aksiyonları gerçek use case'e bağlanır. Testler yalnız screenshot değil; form → API → hesap → persistent result akışını kontrol eder. Accessibility için kontrast/focus/klavye ölçülür; WCAG uyumu ölçülmeden sertifika iddia edilmez.

Önerilen başlangıç ölçümü: 1000 satırlık sonuçta pagination/virtualization, artan dataset boyutunda job progress; preview hedefi tanımlı cihazda p95≤500 ms, uzun backtest için açık ilerleme ve iptal. Bunlar henüz ölçülmüş sonuçlar değildir; P1.19 test raporu cihaz ve veri boyutuyla kaydeder.
