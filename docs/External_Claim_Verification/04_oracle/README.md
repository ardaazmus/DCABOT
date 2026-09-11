# Araştırma oracle’ının sınırı

`arastirma_oracle.py`, yalnız bu paketteki yapay numeric fixture'ları kontrol eder. Production kodu, DCA reducer veya historical adapter implementasyonu değildir. Local acceptance testlerini çalıştırmaz.

Bu klasörde `python arastirma_oracle.py` komutu çalıştırıldığında `oracle_sonucu.json` yeniden oluşturulur. Yalnız Python standart kütüphanesini kullanır; dış servis veya hesap bağlantısı gerekmez.

Kontroller: üç literal fill vector için Decimal/Fraction/literal tablo eşleşmesi; exact quantity conservation; verilen QUOTE fee tutarlarının toplamı; altı strict karşılaştırma; aynı OHLC'yi üreten iki farklı yol; string ve float girdisinin ayrımı. Fee tutarları yeni bir tarife veya formül değildir.

Kontrol edilmeyenler: actual reducer, candidate commit, reserve, anchor, domain maliyet hesabı, net fee asset allocation, late/duplicate olay işleme, production timing, legacy ve recovery. Bu alanlar sonuçta LOCAL-CODE-REQUIRED bırakılır.

Dokümantasyon: [Python Decimal](https://docs.python.org/3/library/decimal.html), [Python Fraction](https://docs.python.org/3/library/fractions.html). Bu kaynaklar sayı semantiği içindir; domain sözleşmesi sağlamaz.
