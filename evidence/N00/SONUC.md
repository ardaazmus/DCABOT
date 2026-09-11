# N00 — Yeni kök başlangıç kanıtı

Tarih: 6 Eylül 2026. Runtime: CPython 3.13.14, Linux x86_64. Çalışma dizini: clean-root/DCABOT. Gerçek komut, stdout/stderr ve exit değerleri [commands.json](commands.json) içindedir.

| Kontrol | Sonuç |
|---|---|
| Yeni bağımlılıksız uv.lock üretimi, frozen offline sync, lock --check | PASS, exit 0 |
| check_workspace.py; boş yedek, yalnız aktif kaynaklar | PASS, exit 0; EMPTY_OR_NOT_PLACED |
| run_checks.py | PASS; 8 test, 0 failure/error/skip |
| run_offline.py | PASS; SCAFFOLD_ONLY, strategy_implemented=false, trading_enabled=false |
| mode=mainnet negatif CLI girdisi | PASS; başarı çıktısı yok, beklenen exit 2 |
| Eksik eski kaynak seçimi | PASS; sahte hash/VERIFIED yok, beklenen exit 2 |

Sekiz test: offline durum, diğer modların reddi, beklenmeyen config alanları, yedeği dolaşmayan discovery, aktif symlink reddi, kaynak dosyasını çalıştırmadan/değiştirmeden hash alma, kapsam dışı yol reddi, eksik aday reddi. Testler geçici sentetik dosyalar kullanır; gerçek kullanıcı yedeğine erişilmedi.

İlk `uv lock --python 3.13 --offline` denemesi interpreter bulunamadığı için exit 2 verdi. CPython 3.13.14 kurulumu sonrası lock/sync/kontroller başarıyla çalıştı. Bu bir ürün testi hatası değildir; ilk ortam eksikliği kayda geçirilmiştir.

## Kapsam ve kalan işler

- implementation=IMPLEMENTED yalnız N00 iskeleti için.
- verification=PASS; evidence_scope=LOCAL_SCAFFOLD.
- review=NOT_RUN: bağımsız ikinci Codex oturumu yapılmadı.
- deployment=NOT_DEPLOYED.
- Kullanıcının Windows/PowerShell ortamı, yerel yedeğin tamlığı ve IDE index dışlama davranışı: NOT_RUN/NOT_VERIFIED. README adımları kullanıcı makinesinde uygulanacak.
- Finansal hesap, DCA, DB/ledger, process daemon, gerçek ağ/testnet/mainnet: NOT_IMPLEMENTED/NOT_RUN.
- Önceki repo incelemesinin sonuçları docs/archive içindedir; bu sekiz teste eklenmez.

N00 yerel kurulum tamamlandığında sıradaki iş TASK.md / N01'dir. Boş bir domain klasörü veya yeşil bootstrap, stratejinin uygulanmış olduğu anlamına gelmez.

## Paket doğrulaması

ZIP bağımsız geçici dizine açıldı; boş YEDEK_ESKI_PROJE ve gerekli kök dosyaları korundu. Açılan kopyada check_workspace, 8 test ve offline CLI doğrudan Python 3.13 ile tekrar geçti. Yeni ortamın .venv veya ilk çalışma dizinine bağımlı olmadığı doğrulandı. [Açılan ZIP kontrolü](extracted_zip_checks.json).
