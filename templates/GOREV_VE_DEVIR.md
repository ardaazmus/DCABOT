# Görev kartı şablonu

```text
Task ID / tek davranış:
Durum / önkoşul:
Taban commit / working tree:
Kullanıcı açısından beklenen sonuç:
Kanonik spec bölüm/karar:
Okunacak yeni kod/test yolları:
Seçilmiş yedek dosyası/sembolü (yoksa NONE):
Kaynak hash → hedef hash / reuse kayıt satırı:
Değişecek kapsam / sınır:
Girdi → doğru sonuç:
Negatif yol / crash / duplicate:
Çalıştırılacak odak komutlar:
Kapanış kanıtı:
Sonraki tek adım:
```

# Devir şablonu

```text
Task ID / implementation durumu:
Base commit → result commit (veya diff hash):
Değişen dosyalar ve neden:
Kabul senaryoları PASS/FAIL/NOT_RUN:
Gerçek komut / cwd / runtime / exit code:
Kanıt dosyası ve scope:
Bağımsız review durumu:
Kalan kritik risk / bilinmeyen:
Ek okunan kaynak ve gerekçesi:
Sonraki tek iş:
```

Kısa devir eski sohbetin özeti değildir; yeni modelin işi sürdürebileceği kaynak adresidir. Secret, imza, credential veya özel hesap yanıtı eklenmez.
