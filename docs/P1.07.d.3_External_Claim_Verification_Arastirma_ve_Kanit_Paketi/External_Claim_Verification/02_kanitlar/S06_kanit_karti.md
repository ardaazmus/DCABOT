# S06 — Immediate Model — Supported Fill Models

- Kurum/yazar: QuantConnect
- Kaynak: [Immediate Model — Supported Fill Models](https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/trade-fills/supported-models/immediate-model)
- Yayın/sürüm: Publication date not stated
- Erişim: 2026-09-09
- İlgili bölüm: Limit Orders, TradeBar rows and following paragraph
- Kanıt türü: EXTERNAL_PRIMARY_SOURCE

Kısa özgün alıntı:

> low price < limit price

Desteklediği sınırlı iddia: TradeBar limit koşulları strict karşılaştırma kullanır; order timestamp verisiyle fill engellenir. Fiyat kuralı her zaman declared limit değildir.

Local modele taşınamayacak sonuç: BASE slice, DCA anchor, fee veya reserve davranışını kanıtlamaz; other data-format rules are distinct.

Bu kart tam sayfa kopyası değildir. Alıntı dışındaki metin analitik açıklamadır.
