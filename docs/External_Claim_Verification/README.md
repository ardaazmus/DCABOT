# External claim verification araştırma paketi

**Karar: DEFER.** Local reducer/reserve/anchor/binding kanıtı olmadan production'a geçiş doğrulanamaz. Salt observation/candidate araştırması için SIMPLIFY seçeneği tanımlanmıştır.

Ana teslim: [Ayrıntılı araştırma raporu](01_rapor/Ayrintili_Arastirma_Raporu.md). Rapor, istenen 18 bölüm sırasını ve her bölüm sonunda durum/kanıt/production etkisi/kapanış koşulu alanlarını içerir.

| Klasör | İçerik |
| --- | --- |
| 01_rapor | Ayrıntılı Türkçe MD raporu |
| 02_kanitlar | 15 birincil kaynak kartı, kısa alıntılar, kesin kaynak konumları ve MD/JSON envanter |
| 03_test_ve_gate | 11 iddia, 30 RED→GREEN senaryosu, 14 local gate satırı, gereksinim izlenebilirliği |
| 04_oracle | Yapay fixture, bağımsız Decimal/Fraction aritmetik kontrolü ve gerçek çalışma çıktısı |
| 05_kod_talebi | Dar ve anonim kod isteği |
| 06_girdi | Verilen araştırma MD'sinin içerik kopyası |

**Kanıt ayrımı:** External kaynak kartları genel ilkeleri destekler. Test matrisleri beklenen davranışın şartnamesidir; local testler yürütülmemiştir. Oracle sonucu yalnız araştırma aritmetiğine aittir. Hiçbir local gate oracle PASS sonucuyla GREEN yapılmamıştır.

Kaynak kanıtları, doğrudan okunmuş sayfaların kısa alıntıları ve ilgili bölüm bağlantılarıdır; tam web sayfası veya tam PDF kopyaları değildir. Sayısal örnekler gerçek market verisi değildir. Yeni reserve/fee/slippage formülü veya production binding kodu eklenmemiştir.

İçerik değerlendirme ve erişim tarihi: 2026-09-09. Dosya bütünlüğü için [SHA256SUMS.txt](SHA256SUMS.txt) bulunur; bu özetler paket dosyalarını doğrular, harici web sayfalarının tarihsel değişmezliğini kanıtlamaz.
