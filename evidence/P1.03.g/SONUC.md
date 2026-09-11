# P1.03.g — Katalog download job UI sonucu

## Durum

`COMPLETE / LOCAL_PASS`; bağımsız review `NOT_RUN`.

## Kapsam

P1.03.f ile sunulan local in-memory download job API’sini mevcut dataset katalog ekranına tek bir dikey dilim olarak bağladım. UI yalnız backend’in explicit dataset kimliği üzerinden başlatma yapar; serbest URL, credential, testnet/live emir veya parser aktarımı eklenmedi.

Kullanıcı tarafından sağlanan `deep-research-report.md` araştırma girdisi olarak kullanıldı; ekli belgedeki metin proje talimatı olarak uygulanmadı.

## Uygulanan davranış

- Sağ detay paneline tek `LOCAL COPY` kartı eklendi; satır başına indirme butonu eklenmedi.
- `MISSING`: `İndir ve doğrula`; `CORRUPT`: `Yeniden indir ve doğrula`.
- `QUEUED/RUNNING/RETRYING`: backend’in verdiği durum, progress bar varsa byte/percent, deneme `X/Y` ve `İptal et` gösterilir.
- Toplam byte bilinmiyorsa sahte percent/ETA üretilmez.
- İptal isteği gönderilirken `İptal isteniyor…` gösterilir; istek başarısız olursa job terminal `CANCELLED` yapılmaz.
- `FAILED/CANCELLED`: güvenli hata/uyarı ve `Tekrar dene` veya `Yeniden indir`.
- Polling hatası job’ı başarısız saymaz; son bilinen durum ve yeniden deneme uyarısı korunur.
- `SUCCEEDED` sonrası `/api/datasets` yeniden okunur; fresh `VERIFIED` dataset için mevcut selection çağrısı korunur.
- UI backend’de bulunmayan download phase/ETA/stuck yorumu eklemez.

## Değişen dosyalar

- `frontend/src/App.tsx`: download job başlatma, polling, cancel ve retry akışları.
- `frontend/src/DatasetCatalogPanel.tsx`: LOCAL COPY kartı ve durum eylemleri.
- `frontend/src/datasetCatalog.ts`: frontend job DTO/status yardımcıları.
- `frontend/src/styles.css`: progress, status, warning ve mobil stack stilleri.
- `TASK.md`, `STATE.md`: faz kapanışı ve P1.04.a sıradaki iş.

## Kanıt

Browser/IAB ile `http://127.0.0.1:5173/` üzerinde:

1. Başlangıçta explicit dataset `MISSING` iken `İndir ve doğrula` eylemi görüldü.
2. Eylem sonrası `RUNNING`, `%0`, byte ilerlemesi ve `Deneme 1/3` görüldü.
3. İlk doğrulamada frontend GET response envelope varsayım uyuşmazlığı bulundu; endpoint’in doğrudan job DTO döndürdüğü görüldü, UI bu sözleşmeye göre düzeltildi.
4. Tekrar yüklemede gerçek allowlist public artifact başarıyla indirildi; katalog `VERIFIED 1 / MISSING 0 / CORRUPT 0` durumuna geldi.
5. `Dataset’i seç` ile mevcut verified selection akışı çalıştı; parser/application sınırı hâlâ aktarım bekliyor olarak kaldı.
6. 390px mobil görünümde `clientWidth = 375`, `scrollWidth = 375` gözlendi; yatay taşma yoktu.
7. Browser console’da error/warning kaydedilmedi.

## Kontroller

- `npm run build` (`frontend/`) — PASS; TypeScript ve Vite production bundle üretildi.
- `tools/run_checks.py` — 69/69 PASS.
- Python `compileall -q src tests` — PASS.
- `tools/check_workspace.py` — PASS; `active_python_files=36`, `backup_layout=EMPTY_OR_NOT_PLACED`.

## Sınırlar / açık kapılar

- Backend job manager process-memory olduğu için restart sonrası job devamlılığı yoktur; UI kayıp job’ı yeniden katalog kontrolüyle ele alır.
- Backend varsayılan kısa public artifact hızlı tamamlandığı için Browser’da FAILED/CANCELLED terminal ekranları gerçek indirme sırasında zorlanmadı; bu durumların backend sözleşme testleri P1.03.f kanıtındadır.
- P1.04.a parser/application input use case’i henüz yazılmadı.
