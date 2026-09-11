# P1.18.c — Read-only explanation UI/UX

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`  
Production readiness: `NO`  
Tarih: 2026-09-10

## 1. Kapsam

Kullanıcı tarafından teslim edilen P1.18.c UI/UX araştırma raporu, mevcut
historical result ekranı ve P1.18.b response contract’ı ile karşılaştırıldı.
Bu dilim yalnız backend’in verdiği `explanations` kayıtlarını salt-okunur
göstermeyi kapsar. UI ekonomik hesap yapmaz, açıklama üretmez, network veya
persistence çağrısı başlatmaz.

## 2. Claim → kontrol → sonuç

### Claim A — Response alanı gerçek sonuç ekranına bağlanabilir

İlk local RED kontrolünde `frontend/src` içinde
`simulation.explanations`, `ExplanationSection` veya `explanations.map`
tüketicisi bulunmadı. P1.18.b response alanı mevcut olmasına rağmen kullanıcı
ekranında görünmüyordu.

Sonuç: UI entegrasyonu gerçekten eksikti; varsayımla değil, kod taramasıyla
doğrulandı.

### Claim B — Yeni bölüm mevcut ekonomik authority’yi değiştirmeden eklenebilir

`DatasetCatalogPanel.tsx` içindeki completed result akışında sonuç değerleri ve
metadata sonrasında; indeterminate akışında incomplete-detail sonrasında yeni
bölüm render ediliyor. `HistoricalChart`, `ActionTable`, API response ve
economic summary değiştirilmedi.

Sonuç: Açıklama projection’ı mevcut API’den okunuyor; frontend yeni PnL, fee,
balance, reserve, exposure veya risk değeri üretmiyor.

### Claim C — Açıklama kayıtlarının denetlenebilir sunumu korunuyor

`ExplanationSection.tsx` severity gruplarını yalnız sunum amacıyla
`ERROR → WARNING → INFO` sırasına alıyor; her grup içindeki backend dizisi
sırası korunuyor. Her kayıt native `<details>` içinde `code`, `source` ve
bounded `context` JSON olarak gösteriliyor. Kayıtlar sessizce gizlenmiyor;
boş liste için açık empty state var.

Sonuç: Backend’in açıklama alanları ekonomik anlamla yeniden sıralanmıyor veya
frontend tarafından dönüştürülmüyor.

## 3. Uygulanan minimum değişiklik

- `frontend/src/ExplanationSection.tsx` adında ayrı, küçük bir sunum bileşeni
  eklendi.
- Completed ve `COMMITTED_PREFIX` içeren indeterminate result akışlarına
  bağlandı.
- Severity renk yerine sembol + metin etiketiyle birlikte gösteriliyor.
- Teknik ayrıntılar native disclosure ile klavye erişimine açık tutuluyor.
- Uzun code/source/context değerleri `overflow-wrap` ve bounded teknik kutuyla
  yatay sayfa taşması oluşturmadan gösteriliyor.
- Mevcut koyu ve yoğun sonuç ekranının yerel token/density yaklaşımı korundu.

## 4. Araştırma raporundan bilinçli olarak ertelenenler

İlk küçük dikey dilimde sticky warning indicator, `sessionStorage`, teknik
ayrıntı kopyalama, `ACTION_RECORDED` özel toplulaştırması ve yeni backend alanı
eklenmedi. Bunlar mevcut kontrat veya ekonomik authority için gerekli değil.

Statik historical sonuç ekranında her WARNING/ERROR kartına `role="alert"`
verilmedi; bu, ekranın her yeniden açılışında assertive ve tekrarlı duyuru
üretme riskini azaltır. Severity metin ve sembolle zaten görünürdür. Daha ileri
NVDA/JAWS davranış testi ayrı erişilebilirlik QA kapısıdır.

## 5. Bağımsız kontrol ve kalite sonucu

```text
frontend npm run build: PASS
tools/run_checks.py: 359/359 PASS
compileall src tests: PASS
tools/check_workspace.py: PASS
active_python_files: 147
frontend/src/ExplanationSection.tsx kapsam taraması:
  network/persistence/economic calculation: YOK
  forbidden financial derivation calls: YOK
```

Tarayıcı tabanlı görsel doğrulama iki kez başlatıldı; Browser çalışma
ortamı `failed to write kernel assets: Sistem belirtilen yolu bulamıyor.`
hatasıyla bağlantı kuramadı. Bu nedenle screenshot, gerçek viewport ve
etkileşim kanıtı `NOT_RUN` bırakıldı; olumlu görsel sonuç iddia edilmedi.

## 6. Karar

```text
IMPLEMENTATION_STATUS=COMPLETE_WITH_LIMITATION
LOCAL_BUILD_AND_REGRESSION=PASS
VISUAL_BROWSER_QA=NOT_RUN_BROWSER_UNAVAILABLE
BACKEND_CONTRACT_CHANGE=NO
PERSISTENCE_CHANGE=NO
FRONTEND_CALCULATION_ALLOWED=NO
LLM_ALLOWED=NO
NETWORK_ALLOWED=NO
ECONOMIC_AUTHORITY_CHANGE=NO
PRODUCTION_READINESS=NO
NEXT_SINGLE_WORK=P1.18.d
NEXT_GATE=VISUAL_ACCESSIBILITY_QA
```

P1.18.d yalnız mevcut bileşenin 320px/390px/desktop görünümünü, disclosure
klavye akışını ve mümkün olduğunda ekran okuyucu davranışını doğrulayacaktır;
bu doğrulama tamamlanmadan görsel erişilebilirlik tamamlanmış sayılmayacaktır.
