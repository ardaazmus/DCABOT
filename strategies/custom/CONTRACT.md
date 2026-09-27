# strategies/custom — yerel özel-strateji sözleşmesi (B.7, BLOCKED)

**DURUM: BLOCKED.** Bu dizin bir TASARIM iskeletidir: kod bağlanmadı,
hiçbir `.py` dosyası yok, motor bu dizini okumuyor. Unblock için Arda'nın
ayrı "yerel plugin API" onayı + sandbox tasarım onayı şarttır. Onaysız
buraya kod konmaz, konulsa bile çalıştırılmaz.

## Amaç

Kullanıcının kendi karar fonksiyonunu yerel dosya olarak bırakıp motora
salt-okunur öneri üretebilmesi (17.19 iskelet). Motor, öneriyi her zaman
kendi doğrulama zincirinden geçirir; plugin asla doğrudan emir üretemez.

## Önerilen imza (taslak, onaylı DEĞİL)

```python
def decision(state: State, config: Config) -> object: ...
```

- `state: State` — `domain.engine.State` salt-okunur görünümü (kopya veya
  dondurulmuş erişim; plugin mutate edemez).
- `config: Config` — `domain.config.Config` salt-okunur görünümü.
- Dönüş tipi HENÜZ KARARLAŞTIRILMADI — `object` yer tutucudur. Adaylar
  (öneri-only enum, guard'lı miktar aralığı vb.) sandbox tasarımıyla
  birlikte onaya sunulacak; bu dilimde ekonomi icat edilmez.

## Saflık kısıtları (önerilen, bağlayıcı olacak)

1. Girdi/çıktı YOK: dosya, ağ, saat, rastgelelik, subprocess yasak.
2. Mutation YOK: `state`/`config` değiştirilemez, global durum yok.
3. Para: `Fraction`/exact-`Decimal` dışı sayı YOK (`float` yasak).
4. Deterministik: aynı `(state, config)` her zaman aynı öneriyi üretir.
5. Sınırlı çalışma: zaman/adım bütçesi sandbox tarafından zorlanır
   (bütçe değerleri tasarım onayında netleşir).

## Unblock koşulları

1. Arda: "yerel plugin API" ürün onayı.
2. Sandbox tasarımı (yükleme, izolasyon, bütçe, hata→fail-closed
   eşlemesi) yazılıp M/F/B disiplininden geçmesi.
3. Dönüş-tip sözleşmesi + motor doğrulama zinciri bağlantısı onayı.
