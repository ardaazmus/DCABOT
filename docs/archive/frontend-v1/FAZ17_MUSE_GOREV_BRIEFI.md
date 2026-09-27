# Faz 17 — Muse Görev Briefi

**Bu dosya muse'un `--trust-workspace` ile doğrudan uygulayacağı görev tanımıdır.** Kod yazmaya başlamadan önce aşağıdaki 3 dosyayı oku:

1. `AGENTS.md` — değişmeyen güvenlik çizgileri (credential/secret/mutation/mainnet: açık onay olmadan **asla**). "Tam yetkili" olman bu çizgileri geçersiz kılmaz.
2. `STATE.md` ve `TASK.md` — projenin şu anki durumu.
3. `docs/ARASTIRMA_FAZ16_QWEN_VIZYON_HARITASI.md` §8 — **yürüteceğin tam harita**: §8.0 araştırma kapıları (RG kodları), §8.1 finansal risk tablosu, §8.2 Lab ilkesi, §8.3 Anti-Liquidation Cascade UI gereksinimi, §8.4 local-first backtest ilkesi, §8.5 TradingView notu, §8.6 BÜYÜK FAZ A-J (uygulayacağın asıl içerik), §8.7 senin için değişmeyen sınırlar.

## Kurallar (bu brief'in üstüne çıkamaz)

- Her küçük dilim için sırayla: **Uygulama → Test** (unit + ilgiliyse checker/gate) **→ Kalite kontrolü** (M/F/B ilgiliyse, değilse kod inceleme + regresyon-sıfır kanıtı) **→ Kabul kriteri → `docs/KARARLAR.md`'ye tek satır, tarihli kayıt.**
- Bir dilime başlamadan önce o dilimin RG (araştırma kapısı) kaynağını **gerçekten aç ve oku** — tahmin etme. RG kodları §8.0'da.
- `src/dcabot/domain/math.py`'ye yazan her değişiklik (BÜYÜK FAZ C, kısmen G/H/I) **küçük, test edilebilir commit'ler** halinde bırakılır — tek büyük commit yok, çünkü bu dosyayı Claude ayrıca doğrulayacak.
- `tools/run_checks.py` kırmızıyken hiçbir büyük faz "kapandı" sayılmaz.
- **Her büyük faz (A, B, C, D, E, F, G, H, I, J) kapandığında:**
  1. `tools/run_checks.py` + frontend testlerini çalıştır.
  2. Uygulamayı build edip ~5 dakika bizzat gez/gözlemle (Genel Bakış → Bot Oluştur → Bot Detay → Deal Detay, o fazla ilgili ekranlar).
  3. **Dur** ve Arda'ya tam olarak şunu sor: **"devam edeyim mi yoksa eklenecek bir not var mı?"** — bu soru sorulmadan, cevap gelmeden bir sonraki büyük faza geçilmez. Bu bir öneri değil, zorunlu insan kapısıdır.
- **BÜYÜK FAZ I**'ye (Profit Currency) başlamadan önce, büyük-faz-sonu durağına ek olarak, Arda'nın bu faza özel, **ayrı "başla" onayını** bekle — `Config.parse`'ın doğrulama mimarisini değiştiriyor.
- **BÜYÜK FAZ D** (Anti-Liquidation Cascade) için ön koşul: gerçek/testnet hesap bağlantısı zaten kurulu olmalı (Faz 3, `p2-testnet-complete`). Değilse bu büyük fazı atla, Arda'ya bildir.
- Likidasyon fiyatını **kendin asla hesaplama** — yalnız borsanın (`positionRisk`) rapor ettiği değeri oku/göster (LCR-12, değişmez).
- Whale Wall Detection ve borsayı yoran her özellik, §8.2'deki `lab_rate_budget.py` bütçesine tabi olmadan canlı hale gelmez.

## Sıra

BÜYÜK FAZ **A → B → C → D → E → F → G → H → I → J** (§8.6'daki tam içerik ve kabul kapılarıyla).

## Başlangıç

BÜYÜK FAZ A'nın ilk dilimi olan **A.1**'i (lightweight-charts entegrasyonu) §8.6'daki tanımla birebir uygula. Herhangi bir belirsizlikte kod yazmadan önce durup sor.
