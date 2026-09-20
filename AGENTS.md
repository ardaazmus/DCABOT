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
Dur ve Arda'ya kısa, tek soru sor: credential/hesap gerektiğinde; ürün veya ekonomi kararı gerektiğinde; gerçek emir gerektiğinde; bir araştırma oturumundan sonra kanıt hâlâ yetersizse.
Araştırma kutusu: bir belirsizlik için en fazla bir oturum. Çıktı: ≤ 10 satır karar notu (`docs/KARARLAR.md`) + soru. Belirsizliği kapatmak için yeni "güvenli dilim" üretme. `NO-GO` / `DEFERRED` "durdum, karar bekliyor" demektir.

## Ajanlar arası işbölümü
Kritik dosyalar (`src/dcabot/domain/`, `application/historical_simulation.py`, `application/historical_run_contract.py`, `persistence/`, her Decimal/Fraction/hash hesabı) yalnız Claude değiştirir. UI-only, backend'e dokunmayan dilimler başka bir ajana (ör. Codex) TASK.md üzerinden, dosya allowlist'li bir brief ile devredilebilir; devralan ajan STATE.md/TASK.md/docs/KARARLAR.md'yi değiştirmez, yalnız kodu+testini yazar ve brief'teki durma koşullarına uyar. Claude her devirden sonra diff + tam checker + frontend tsc/vitest ile kontrol eder, belgeleri kendisi günceller.

## Boyut limiti
Bayt olarak `tools/check_workspace.py` zorlar: AGENTS/STATE/TASK/WORKFLOW ≤ 6 KB, docs/YOL_HARITASI ≤ 10 KB, CLAUDE/GEMINI/OPENCODE ≤ 1 KB. Limit aşılırsa içeriği kısalt, limiti büyütme.
