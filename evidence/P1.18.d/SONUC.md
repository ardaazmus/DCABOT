# P1.18.d — Read-only explanation visual/accessibility QA

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`  
Production readiness: `NO`  
Tarih: 2026-09-10

## Karar

P1.18.d kapatıldı. Browser eklentisinin kernel-assets hatası nedeniyle çalışmaması
fazı açık bırakmadı; aynı yerel frontend + backend akışı doğrudan kurulu Chrome'un
CDP arayüzüyle doğrulandı. Bu fallback yalnız yerel görsel/etkileşim QA'sı içindir;
canlı ağ, credential, emir veya ekonomik authority açılmadı.

## Claim → control → result

| İddia / kabul ölçütü | Kontrol | Sonuç |
|---|---|---|
| Sonuç ekranında backend açıklamaları görünür | Sabit dilimli tarihsel demo gerçek yerel akışta çalıştırıldı; DOM'da `8` explanation ve `8` explanation card bulundu | `PASS` |
| Severity sunumu okunabilir ve backend grup-içi sırası korunur | Desktop ve mobil render, visible severity text/symbol ve card sırası kontrol edildi | `PASS` |
| 320px/390px mobil görünümde sayfa taşmaz | Chrome viewport ölçümü: 390px'te `scrollWidth=375 <= innerWidth=390`; 320px'te `scrollWidth=305 <= innerWidth=320` | `PASS` |
| Teknik ayrıntı disclosure'ı klavyeyle çalışır | Native `<details>/<summary>` odağı doğrulandı; Space ile aç/kapa gözlendi | `PASS` |
| UI ekonomik hesap yapmaz veya dış veri çağırmaz | Statik UI contract taraması; `fetch`, storage, clipboard, numeric parse ve `Math.random` yok | `PASS` |
| Derleme ve mevcut davranış bozulmaz | Frontend build, Python regresyon, compile ve workspace kontrolleri | `PASS` |

## Görsel kanıtlar

- Desktop: `D:\project\DCABOT\.cluster\P1.18.d-visual-qa\DELIVERY\result-1280.png`
- Mobil 390px: `D:\project\DCABOT\.cluster\P1.18.d-visual-qa\DELIVERY\result-390.png`
- Mobil 320px: `D:\project\DCABOT\.cluster\P1.18.d-visual-qa\DELIVERY\result-320.png`

Görüntülerde sonuç özeti altında açıklama bölümü, üç WARNING ve beş INFO kartı
stacked biçimde görünür. Uzun teknik içerik doğal satır kırılmasıyla sayfa
genişliğini aşmaz.

## Çalıştırılan kontroller

```text
Browser plugin: FAILED — failed to write kernel assets
Direct Chrome CDP fallback: PASS
Frontend npm run build: PASS
Python regression: 359/359 PASS
Python compileall: PASS
Workspace check: PASS
Static UI contract: PASS
```

## Sınır ve açık kanıt

Ekran okuyucuya özgü NVDA/JAWS testi bu ortamda çalıştırılmadı:
`SCREEN_READER_QA=NOT_RUN`. Bu nedenle sonuç production accessibility certification
değil, yerel visual/accessibility smoke QA kabulüdür. Native disclosure semantiği ve
Space klavye etkileşimi doğrulanmış olsa da NVDA/JAWS sonucu iddia edilmemelidir.

### NVDA kurulum ve başlatma kontrolü

Kullanıcı izniyle resmi NVDA 2026.2 paketi doğrulanmış SHA-256 ile indirildi ve
sistem kurulumunun UAC gerektirdiği görülünce kalıcı kurulum yerine yalnız bu kanıt
görevi altında taşınabilir kopya oluşturuldu:

```text
Portable path: D:\project\DCABOT\.cluster\NVDA-screen-reader-qa\portable
Creation mode: --create-portable-silent
Start-on-logon: not enabled
NVDA executable: present
NVDA initialization: PASS
Speech engine: eSpeak fallback initialized
Speech Viewer / Chrome focus traversal: NOT_RUN
```

NVDA logu `NVDA initialized` satırını ve eSpeak sürücüsünün yüklendiğini gösteriyor.
Bu ortamın etkileşimli Windows masaüstü olmadığı için NVDA menüsü, Speech Viewer ve
gerçek Chrome odağı arasında kullanıcı seviyesinde geçiş yapılamadı. Taşınabilir
NVDA'nın başlatılmış olması, ekran okuyucu kabul testinin tamamlandığı anlamına
gelmez; bu nedenle `COMPLETE_WITH_LIMITATION` kararı korunmuştur.

Enter tuşu için bağımsız geçerli gözlem alınmadı; bu nedenle Enter davranışı ayrıca
kanıtlanmış sayılmadı. Native button/disclosure sözleşmesi mevcut olduğundan yeni
kod değişikliği yapılmadı.

## Korunan sınırlar

Yeni ekonomik alan, frontend hesabı, backend contract değişikliği, persistence,
network, LLM, sticky notification, clipboard veya gerçek işlem yolu eklenmedi.

```text
VISUAL_BROWSER_QA=PASS
CHROME_CDP_FALLBACK=PASS
MOBILE_320_QA=PASS
MOBILE_390_QA=PASS
DESKTOP_QA=PASS
KEYBOARD_SPACE_DISCLOSURE_QA=PASS
SCREEN_READER_QA=NOT_RUN
NVDA_PORTABLE_INITIALIZATION=PASS
NVDA_SPEECH_VIEWER_QA=NOT_RUN_ENVIRONMENT_LIMIT
LOCAL_STATIC_CHECK=PASS
IMPLEMENTATION_GATE=COMPLETE_WITH_LIMITATION
NEXT_SINGLE_WORK=P1.19.a
```
