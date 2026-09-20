# P1.12.f.h.t — Profile source provenance/snapshot identity karar kapısı

**Tarih:** 2026-09-17  
**Durum:** `CONTRACT_READY / IMPLEMENTATION_PENDING`; persistence/migration `NO-GO`

## Karar

Profile revision’ın güvenilir source kanıtı sayılması için revision ile birlikte
ayrı provenance kaydı gerekir. Minimum kayıt:

- bounded source kind ve source row/snapshot identity;
- alınan exact payload’ın SHA-256 hash’i;
- source schema/policy revision identity’si;
- integer observed time ve profile revision bağı.

Aynı source identity farklı payload hash’iyle tekrar gelirse `CONFLICT`; aynı
identity ve hash exact `DUPLICATE`; eksik/bozuk/UNKNOWN source ise
`QUARANTINED` veya `NO_GO` kalmalıdır. Bu provenance kaydı contract-size veya
fee/slippage/rounding değerlerini üretmez; yalnız bunların hangi immutable
source snapshot’tan geldiğini kanıtlar.

## Mevcut durum

V1 `profile_revisions` tablosu provenance kind/row/hash/time alanlarını
taşımıyor. Bu nedenle mevcut adapter profile revision üretebilse de source
provenance’ı kalıcı authority olarak sunamaz. Schema version yükseltme veya
ayrı provenance tablosu kararı olmadan migration açılmayacak.

Bu karar kapısında üretim kodu değişmedi. Mevcut explicit source adapter hedefli
`2/2 PASS`, son tam proje kapısı `545/545 PASS` durumundadır.

## Sonraki tek iş

Provenance kaydının v1 journal’a ayrı immutable sahip olarak eklenmesi için
schema/migration taslağını hazırlamak; failure/replay ve conflict kanıtı
olmadan profile migration’ı `NO-GO` tutmaktır.
