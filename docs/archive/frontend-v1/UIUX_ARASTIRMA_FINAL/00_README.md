# 00_README — Faz 11 UI/UX araştırma paketi

RESEARCH_COMPLETE: YES (2 bağımsız rapor)
RESEARCH_DATE: 2026-09-21
PACKAGE_ROOT: `UIUX_ARASTIRMA_FINAL/`
LOCAL_CODE_INSPECTED: NO (raporların kendisi; bu README'de Claude tarafından `frontend/src/` ile çapraz kontrol edildi)

## İçerik
- `01_RAPOR_A.md` — birinci bağımsız anonim araştırma raporu (28 bölüm, karar matrisi + kaynak kaydı).
- `02_RAPOR_B.md` — ikinci bağımsız anonim araştırma raporu (51+ kaynak, CONFIRMED/CONDITIONAL/JUDGMENT sınıflı, çok daha ayrıntılı).

Her iki rapor da anonim promptla (proje adı/dosya yolu içermeyen, genel "10+ modüllü çok-stratejili trading dashboard" çerçevesi) üretildi ve bilinçli olarak yüksek-kontrast/ekran-okuyucu erişilebilirliğini kapsam dışı bıraktı (ayrı iz: Faz 9/F30).

## Yakınsama
İki rapor birbirinden bağımsız olarak neredeyse aynı mimariye ulaştı:
- kalıcı sol navigasyon + evrensel üst bar + entity-context header + sınırlı in-page tabs,
- strateji aileleri nav öğesi değil, "Botlar/Stratejiler" içinde tür/filtre,
- progressive disclosure alan/bölüm seviyesinde, global Basit/Uzman mod anahtarı yok,
- yeni-kurulum=sihirbaz, düzenleme=tek-sayfa-bölümlü-form + canlı önizleme,
- çoklu bot izleme: kart-özet → virtualized tablo → detay,
- 5 kanallı bildirim taksonomisi (toast/banner/section-status/merkez+rozet/onay-diyaloğu),
- 3 katmanlı semantic design token mimarisi (açık/koyu tema),
- gerçek-zamanlı render: abone-bazlı seçici güncelleme + throttle/batch + virtualization + code-splitting + ölçülmüş memoization.

## Tek ayrışma noktası
Rapor A üst navigasyonda 8 bölüm önerdi (Overview/Automation/Portfolio/Monitor/Simulation/Alerts/Audit&Export/Settings). Rapor B, Material Design 3'ün "5'ten fazla nav hedefi koyma" kısıtını doğrudan birincil kaynaktan (`m3.material.io/components/navigation-bar/guidelines`) alıntılayarak 5 bölüme indirdi (Genel Bakış/Botlar & Stratejiler/Piyasa & Veri/Olaylar & Denetim/Ayarlar). Rapor B'nin kaynak zinciri daha sıkı (51 kaynak, her karar için doğrudan alıntı + CONFIRMED/CONDITIONAL/JUDGMENT sınıfı; Rapor A'da aynı titizlik yok — 8-bölüm önerisi hiçbir yerde "CONFIRMED" değil).

**Karar: Rapor B'nin 5-bölümlü modeli esas alındı.** Rapor A'nın ayrı "Monitor" (cross-bot pozisyon/emir) fikri kaybolmuyor — Genel Bakış'ın özet görünümü ve Botlar & Stratejiler'in filtrelenebilir tablosu üzerinden karşılanıyor, ayrı bir nav hedefi olarak değil.

## Mevcut koda karşı analiz (Claude, 2026-09-21)
`frontend/src/App.tsx` şu an tek bir "studio" iş alanı: sidebar'da "Bot stüdyosu" (aktif), "Ayarlar"/"Planlar" (disabled placeholder), "Geçmiş" (Saved Runs). Hiç breadcrumb, hiç entity-context header, hiç tab yok — form/ladder/özet panelleri doğrudan tek sayfada yan yana. `styles.css` yalnız 6 düz `--ui-*` custom property tanımlıyor (`:root { --ui-bg-body: #09121c; ... }`), `[data-theme]` bağlamı veya açık tema hiç yok — 3 katmanlı token mimarisinin hiçbir seviyesi mevcut değil.

Bu, her iki raporun da temel uyarısını (düz navigasyon + component-level hardcoded renk, 10+ modülde ölçeklenmez) doğrudan doğruluyor: mevcut yapı bugünkü haliyle Faz 5-10'un 20 F-kodunu kaldıramaz.

## Sonraki adım
docs/YOL_HARITASI.md Faz 11'de özetlenen 9 maddelik tasarım kararı — implementasyon henüz başlamadı, Arda'nın onayını bekliyor. Tam gerekçe ve kaynak alıntıları: docs/KARARLAR.md 2026-09-21 "Faz 11 tasarım kararı".
