# Faz N2 sonuç — Telegram bildirimi (2026-09-27, Muse)

## Kapsam
EventLog landmark → Telegram sohbetine fan-out: 15 sn worker, cursor
ile en-az-bir-kez gönderim, hata durur/sonraki tur tekrar dener.
Token OS kasasında (`DCABOT:NOTIFY` ad alanı), chat/cursor/hata
`notifications.sqlite3` içinde; token yanıtta/logda asla yok.
API: durum/kaydet/test/aç-kapa/unut. UI: bildirim sayfası kartı.

## Kanıt (LOCAL)
- checker 2430/2430 (17 yeni), vitest 247/247 (3 yeni)
- tsc + lint temiz; notifications e2e 3/3 (sahte kimlikle kasa turu)
- Canlı gönderim kanıtı YOK: gerçek bot token + chat id gerekli.

## Açık
Arda'ya tek soru: Telegram bot token + chat id verilecek mi?
Evet ise: kaydet → test gönder → BEKLEYEN landmark akışı kanıtlanır.
