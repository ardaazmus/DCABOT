# DCABOT — ajan kuralları

Amaç: gerçekten çalışan bir DCA/grid trading ürünü. Sıra: P1 yerel demo → P2 Binance testnet → P3 gerçek Binance (sınırlı canary) → P4 diğer borsalar. Ürün tanımı `docs/URUN_KAPSAMI.md`, güncel sıra `docs/YOL_HARITASI.md`, kapsam tablosu `docs/OZELLIK_MATRISI.md`. Belgeler Türkçe, kod ve tanımlayıcılar İngilizce.

## Güvenlik çizgileri (değişmez)
1. Repo public. Credential, secret, imzalı hesap yanıtı hiçbir dosyaya, fixture'a, loga, prompta girmez.
2. Emir gönderimi ve mainnet yalnız Arda açıkça isterse. Testnet mutation ayrı, yazılı onaylı bir gate ister.
3. Para: sonlu Decimal/string girişi, iç hesap exact Fraction. Finansal UI hesabı ve `Number` yok; çekirdek tek doğruluk kaynağıdır, UI onu gösterir.
4. Plan/status dolum değildir. UNKNOWN, eksik veri ve gap temiz kanıt sayılmaz; kör yeniden POST yok.
5. Aynı ekonomik olay yalnız bir kez kaydedilir (kimlik, dedup, idempotency).
6. `YEDEK_ESKI_PROJE/` salt okunur başvurudur; topluca yükleme/çalıştırma. Aktarım `docs/YEDEKTEN_AKTARIM.md` ile.

## Çalışma biçimi
- Oturum başında yalnız AGENTS.md, STATE.md, TASK.md oku. Gerisini göreve göre aç. `docs/archive/` ve `evidence/archive/` varsayılan olarak okunmaz.
- Bir iş = kullanıcının görebileceği veya çalıştırabileceği bir sonuç (ekran, komut, gerçek testnet davranışı). Küçük dikey dilim: giriş → hesap/kayıt → test.
- Aynı alt sistemde art arda en fazla 3 dilim (sayaç TASK.md'de). Sonra YOL_HARITASI'ndaki bir sonraki ürün adımına geç. "Bir regresyon daha" kendi başına iş değildir.
- Sıradaki işi `docs/YOL_HARITASI.md` "Şimdi" bölümünden seç; bir önceki işin varyasyonundan değil.
- Hata düzeltmede önce başarısız test, sonra minimal kod. Ağ ve saat yerine tipli girdi veya fake port kullan.
- Kontrol: değişen alanın testleri + `uv run --frozen python tools/run_checks.py` (Python 3.13). Frontend değiştiyse: `cd frontend && npx tsc -b && npx vitest run`.
- Yerel PASS, REAL_TESTNET kanıtı değildir. Durum eksenleri WORKFLOW.md'de.
- Faz sonunda bağımsız inceleme (başka model/oturum, salt okunur). Yapılmadıysa `review=NOT_RUN` yaz. Dilim başına şart değil.
- Belgeler: STATE.md ve TASK.md'yi ÜZERİNE YAZ, ekleme yapma; geçmiş git'tedir. Yeni MASTER/FINAL/araştırma belgesi açma. Kanıt: faz başına tek `evidence/<faz>/SONUC.md` (≤ 60 satır); dilim başına klasör açma.
- `OZELLIK_MATRISI` hücresi tek satır durum tutar (PLAN / KISMEN / LOCAL / TESTNET). Dilim günlüğü oraya yazılmaz.

## Durma ve sorma
**Yetki (Arda, 2026-09-26, bağlayıcı):** Proje bitene kadar tüm ürün, ekonomi ve kapı kararlarını Muse verir; Arda'ya soru sorulmaz. Her karar `docs/KARARLAR.md`ye yazılır ve uygulanır. Araştırma kutusu: belirsizlik başına bir oturum, çıktı ≤ 10 satır karar notu. Fiziksel sınır soru değildir: credential/anahtar yoksa paper/kayıtlı-fixture ile devam edilir, eksik belgeye not edilir. Yetki ≠ emir: gerçek emir için ayrıca açık emir gerekir; anahtar yokken mainnet/testnet mutation kapıları kapalı tutulur.

## Çalışma düzeni (tek yapay zeka)
**Bağlayıcı (Arda, 2026-09-26):** Tek yapay zeka Muse'dur; backend, arayüz, test ve belgelerin tümü ondadır. 2026-09-23 işbölümü (Claude/muse brief/devret döngüsü) GEÇERSİZDİR. Kritik-dosya kısıtı kalktı; finans disiplini (Güvenlik çizgileri m.3) aynen sürer. "Kim yaptı" bilgisinin tek doğru kaynağı `docs/KARARLAR.md`dir.

## Boyut limiti
Bayt olarak `tools/check_workspace.py` zorlar: AGENTS/STATE/TASK/WORKFLOW ≤ 6 KB, docs/YOL_HARITASI ≤ 10 KB, CLAUDE/GEMINI/OPENCODE ≤ 1 KB. Limit aşılırsa içeriği kısalt, limiti büyütme.
