# P1.05.d — Minimal ekonomik sonuç özeti sonucu

Durum: COMPLETE / LOCAL_PASS_WITH_LIMITATION  
Tarih: 2026-09-07  
Review: NOT_RUN

## Karar girdisi ve yorumlama

Kullanıcı tarafından sağlanan `P1.05.d_Minimal_Ekonomik_Sonuc_Detayli_Arastirma_Raporu.md`, proje talimatı olarak değil araştırma çıktısı olarak değerlendirildi. Raporun ana kararı şudur: minimum görünüm yalnız gross realized, fee, model net realized, position status ve açık sınırlama notlarından oluşmalı; `unrealized` ve `equity` sayısal olarak ertelenmelidir.

Araştırma raporundaki unit/currency ve “all costs” blocker’ları mevcut kaynak kodla ayrıca doğrulandı:

- `Config.parse` mevcut P1 config’te yalnız `quote_asset=USDT` kabul eder.
- Run-plan aynı config snapshot’ının `quote_asset` değerini frontend’e taşır.
- Position cost, realized değer, fee, funding, entry notional ve equity domain’de quote-asset bağlamındadır.
- Historical fill fee’si `config.quote_asset` olarak kaydedilir.
- `realized_net_after_all_costs` domain’de `realized - fees - funding` olarak üretilir.
- Historical OHLCV akışında funding üretilmez; sonuç `funding_status=NOT_MODELED` taşır.
- `mark_status=NOT_AVAILABLE` olduğundan `unrealized` ve `equity` kullanıcıya kesin numeric valuation olarak gösterilmez.

Bu açıklama yeni endpoint veya yeni finansal formül değildir; mevcut v1 davranışının UI sözleşmesine açıkça bağlanmasıdır.

## Uygulanan minimum davranış

Tamamlanmış sonuçta, mevcut backend stringleri doğrudan ve yeniden hesaplanmadan şu sırayla gösterilir:

1. `Brüt gerçekleşen sonuç · USDT` — `summary.realized_gross`
2. `İşlem ücretleri · USDT` — `summary.fees`
3. `Model net gerçekleşen sonuç · USDT` — `summary.realized_net_after_all_costs`
4. `Pozisyon durumu` — `CLOSED` veya `OPEN_AT_END`

Ek güvenli açıklamalar:

- Değerlerin backend modelinden geldiği ve UI’da yeniden hesaplanmadığı belirtilir.
- Funding’in tarihsel modelde işlenmediği belirtilir; numeric `funding` gösterilmez.
- Exchange mark mevcut olmadığı için `unrealized` ve `equity` numeric olarak gösterilmez.
- `OPEN_AT_END` için forced close uygulanmadığı ve dönem sonu pozisyonunun açık kaldığı belirtilir.
- `persisted=false` ve gerçek emir/testnet kapsam dışı notları korunur.

`INDETERMINATE / AMBIGUOUS_OHLC_PATH` mevcut davranışla ekonomik özet göstermez. `anchor`, `take_profit_price`, `cost`, `qty` ve `entry_notional` bu minimum sonuç kartına eklenmez.

## Değişen dosyalar

- `frontend/src/DatasetCatalogPanel.tsx` — minimum ekonomik değerlerin güvenli etiketlerle gösterimi; unrealized/equity numeric görünümünün kaldırılması.
- `docs/VERI_VE_SIMULASYON.md` — v1 ekonomik alan birimi ve net sonuç bileşimi clarification.
- `TASK.md`, `STATE.md`, `README.md` — P1.05.d durumu ve sonraki P1.06 fazı.
- `evidence/P1.05.d/SONUC.md` — bu kanıt.

## Kapsam dışı bırakılanlar

Bu fazda aşağıdakiler yapılmadı:

- Frontend finansal aritmetik veya rounding
- Yeni backend endpoint/response alanı
- `unrealized` veya `equity` sayısal değerinin gösterimi
- Numeric funding
- ROI/return %, drawdown, Sharpe, Sortino, CAGR
- Equity curve veya benchmark
- Çoklu koşu karşılaştırması
- Export, persistence, kopyalama
- Tooltip, hover, count-up veya animasyon

## Doğrulama

Komut:

```powershell
cd D:\project\DCABOT\frontend
npm run build
```

Sonuç: PASS. TypeScript derlemesi ve Vite production build tamamlandı.

Backend kodu ve API sözleşmesi değiştirilmedi. P1.05.c.1 sonrası kanıtlı Python regresyonu 82/82 PASS olarak korunuyor; bu alt faz frontend ve sözleşme dokümantasyonu ile sınırlı olduğu için yeniden çalıştırılmadı.

Gerçek local UI smoke’unda mevcut `config/paper.json` ile gerçek artifact fiyat ölçeği uyumsuzluğu nedeniyle simülasyon güvenli `422 REDUCER_POLICY_REJECTED` döndürdü; UI hata mesajını gösterdi ve sonuç kartını açmadı. Bu nedenle `COMPLETED` ekonomik kartı sentetik veriyle doğrulanmadı. Aynı QA koşusunda desktop `body.scrollWidth=clientWidth=1265`, 320px viewport’ta `body.scrollWidth=clientWidth=305` ve `pageOverflow=false` görüldü. Console error/warning yoktu. Başarı ekranı için uyumlu gerçek config/artifact ayrıca gereklidir.

## Faz kararı

P1.05.d’nin minimum davranışı uygulanmıştır. P1.05 sonuç inceleme ailesi; güvenli summary, action table, OHLC overview, action marker ve minimal economic outcome katmanlarına sahiptir. Sıradaki planlı faz P1.06’dır: koşuyu kaydetme, yeniden açma, tekrar üretme ve karşılaştırma için persistence/run identity sözleşmesi. Bu faz başlamadan yeni kalıcı kayıt veya karşılaştırma kodu yazılmayacaktır.
