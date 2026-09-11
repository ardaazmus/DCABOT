# P1.06.f.2 — Historical profile seçimi UI sonucu

Durum: COMPLETE / LOCAL_PASS; bağımsız review: NOT_RUN.

## Kapsam

Kullanıcı tarafından sağlanan UI/UX araştırma raporu talimat olarak değil, doğrulanacak tasarım kanıtı olarak incelendi. Kabul edilen en küçük dilim; doğrulanmış dataset preflight kartında native profile select, explicit kullanıcı seçimi, backend run-plan eşleşmesi, kalıcı `project_fixture` uyarısı ve stale sonuç temizliğidir.

## Uygulanan kararlar

- İlk durumda `paper` dahil hiçbir profil otomatik seçilmez; `Profil seçin…` placeholder’ı görünür.
- Profil etiketleri ve beklenen dataset eşleşmesi backend sözleşmesinden gelir; frontend sembol/interval üzerinden profil türetmez.
- Profil değişince eski run-plan, simülasyon, grafik ve save durumu temizlenir; yalnız güncel dataset/profile isteği kabul edilir.
- Run-plan yalnız explicit profil seçimi ve güncel preflight sonrasında istenir; simulation payload `profile_id` taşır.
- `project_fixture` için kırmızı hata veya ek confirmation yerine kalıcı inline bilgi notu gösterilir.
- Native select korunur; custom keyboard davranışı ve yeni dashboard/modal eklenmez.

## Kontrol → test → farklı kontrol → sonuç

1. API sözleşmesi kontrolü: `HistoricalProfileResponse` artık `label` ve `expected_dataset_id` taşıyor; `run-plan` ve simulation response’ları aynı profile snapshot’ını taşıyor.
2. Backend test kontrolü: `uv run --frozen python tools/run_checks.py` — `113/113 PASS`.
3. Farklı statik kontrol: `PYTHONPATH=src; uv run --frozen python -m compileall -q src tests` ve `uv run --frozen python tools/check_workspace.py` — PASS; workspace `errors=[]`.
4. Frontend contract kontrolü: `npm run build` — TypeScript ve Vite build PASS.
5. Gerçek local UI kontrolü: güncel Uvicorn ile IAB desktop akışında profil listesi, boş seçim ve demo profil run-plan’ı görüldü; console error yok.
6. Fail-closed UI kontrolü: profil seçilmeden simülasyon başlatma butonu DOM’da yok; explicit demo seçiminden sonra tek buton ve `project_fixture` note göründü.
7. Responsive kontrol: 320×844 viewport’ta `document.scrollWidth=305`, viewport genişliği `320`; yatay overflow yok, select ve warning görünür.
8. Farklı UI state kontrolü: tamamlanmış demo simülasyonundan sonra profil `paper` olarak değiştirildi; eski sonuç temizlendi, güncel profil planı dışında eski chart/save sonucu kalmadı.

## Sınırlar

- `paper` profilinin bu tarihsel artifact üzerinde ekonomik olarak uygunluğu bu fazda yeniden yorumlanmadı; mevcut backend pairing sözleşmesiyle ayrı bir valid profil olarak gösterilir ve config değiştirilmez.
- Bağımsız repository review çalıştırılmadı; bu nedenle review durumu `NOT_RUN` bırakıldı.
- Profil düzenleme, yeni profil oluşturma, compare/re-run/export ve gerçek venue/testnet bağlantısı kapsam dışıdır.
