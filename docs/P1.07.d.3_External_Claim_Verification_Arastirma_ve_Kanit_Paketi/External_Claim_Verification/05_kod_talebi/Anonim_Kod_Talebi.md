# Anonim ve dar kod talebi

Lütfen yalnız aşağıdaki anonim kod parçalarını gönderin:

1. **State/Order/Position ve immutable value type tanımları:** sınıf/fonksiyon adlarını koruyun; özel dosya yolu, proje adı, kullanıcı adı ve gerçek sembol değerlerini maskeleyin. Role, side, quantity, price, placement identity, model/config identity, pending/unsettled, final/coverage ve anchor alanlarının tanımı yeterlidir.
2. **Event reducer:** INTENT, FILL, ORDER_FINAL, UNKNOWN ve MARK branch’lerini; bunların çağırdığı reserve/blocker/anchor güncellemelerini gönderin. Ekonomik state’e ulaşan ilgili çağıran bölümü de dahil edin. Dış servis ve kimlik bilgisi satırlarını çıkarın.
3. **Risk ve strateji karar fonksiyonları:** pending order, commitment/reserve gate, BASE anchor, safety ladder/index/coverage ve next-decision blocker hesabını gösteren dar parçalar yeterlidir. Bütün strateji dosyası gerekmez.
4. **Historical decision adapter ve fixed-limit policy:** bar index/time, closed-bar doğrulaması, placement/eligible kararı, observation/result dataclass’ları, trigger, candidate payload’ı ve reducer çağrısını gönderin.
5. **Exact conversion ve identity yardımcıları:** fee/slippage sahipliği, quantity/tick dönüşümü ve config hash/model-version canonicalization’ının ilgili anonim bölümlerini gönderin. Mevcut dedupe veya kayıt üzerinden replay davranışı varsa yalnız ilgili küçük parça yeterlidir; yeni persistence tasarımı istenmiyor.
6. **İlgili testler:** test adı, fixture, açık event sırası, beklenen state/result; duplicate, yeni late fill, ambiguity, EOF, partial/full BASE, reserve ve legacy vakalarını gönderin. Beklenen değeri aynı production helper’ından üreten kısmı varsa açıkça belirtin.

Whole repository, bütün test klasörü, secret, `.env`, credential, veritabanı dökümü, private URL, gerçek hesap kimliği veya kişisel path göndermeyin. Kod yalnız tasarım örneğiyse **PROPOSED DESIGN** olarak etiketleyin; bu, çalışmakta olan implementasyon kanıtı sayılmayacaktır.

Kod geldiğinde önce sembolün gerçekten çağrı zincirine bağlılığı, sonra event sırası ve mutasyon sahibi incelenmelidir. Testin kendi expected sonucunu aynı production helper ile üretip üretmediği ayrıca denetlenmelidir. Tek bir sembol eksikliği değerlendirmeyi engellerse sadece o parça ve kapattığı claim istenmelidir. Bu aşamada geniş repository, yeni API veya migration çalışması talep edilmez.


