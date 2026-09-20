"""Tek seferlik temizlik: geçmiş belge ve kanıtları arşive taşır.

Varsayılan dry-run'dır (hiçbir şey değiştirmez). Uygulamak için: --apply

Yaptıkları:
1. STATE/TASK/AGENTS/WORKFLOW/YOL_HARITASI/OZELLIK_MATRISI'nin HEAD sürümünü
   docs/archive/history/ altına tam kopya olarak kaydeder.
2. docs/ içindeki aktif olmayan belgeleri (araştırma promptları, raporlar, zip'ler)
   docs/archive/research/ altına git mv ile taşır.
3. evidence/ içinde son fazlar dışındaki klasörleri evidence/archive/ altına taşır
   ve evidence/INDEX.md üretir.
4. docs/OZELLIK_MATRISI.md'yi sıkıştırır (dilim günlükleri gider, tablo kalır,
   "Bugünkü durum" hücreleri kısaltılır; tam metin arşivdedir).
5. Kalan .md dosyalarındaki taşınmış yolları günceller (docs/X, evidence/X).
6. .ignore'a arşiv yollarını, README'ye bağımlılık düzeltmesini ekler.

Yeni AGENTS/STATE/TASK/WORKFLOW/YOL_HARITASI dosyalarını bu betik YAZMAZ; onları
betikten SONRA kökün üzerine kopyalarsınız (eski sürümler zaten arşivlendi).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATE = "2026-09-20"

SNAPSHOTS = (
    "STATE.md",
    "TASK.md",
    "AGENTS.md",
    "WORKFLOW.md",
    "docs/YOL_HARITASI.md",
    "docs/OZELLIK_MATRISI.md",
)
KEEP_DOCS = {
    "archive",
    "CEKIRDEK_KULLANIM.md",
    "DOGRULAMA.md",
    "EMIR_VE_KURTARMA.md",
    "GECIS.md",
    "KARARLAR.md",
    "KAYNAKLAR.md",
    "MATEMATIK.md",
    "MIMARI.md",
    "OZELLIK_MATRISI.md",
    "UI_UX.md",
    "URUN_KAPSAMI.md",
    "VERI_VE_SIMULASYON.md",
    "YEDEKTEN_AKTARIM.md",
    "YOL_HARITASI.md",
}
KEEP_EVIDENCE = {"archive", "P2.03", "P2.04", "P2.04.c", "P2.05"}
MATRIX_CELL_LIMIT = 220

README_OLD = (
    "Harici Python bağımlılığı yok; ilk Python/uv kurulumu internet gerektirebilir. "
    "Çalışma akışı ağ kullanmaz."
)
README_NEW = (
    "Çekirdek CLI (`tools/bot.py`) yalnız standart kütüphane kullanır. Tam test paketi ve "
    "yerel API/arayüz için `uv sync --frozen` gerekir (FastAPI, uvicorn, websockets); "
    "Python 3.13 zorunludur. Çekirdek çalışma akışı ağ kullanmaz."
)


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def is_tracked(rel: str) -> bool:
    return git("ls-files", "--error-unmatch", "--", rel, check=False).returncode == 0


class Plan:
    def __init__(self, apply: bool) -> None:
        self.apply = apply
        self.moves: list[tuple[str, str]] = []
        self.notes: list[str] = []

    def say(self, message: str) -> None:
        print(message)

    def move(self, src: str, dst: str) -> None:
        self.moves.append((src, dst))
        if not self.apply:
            return
        (ROOT / dst).parent.mkdir(parents=True, exist_ok=True)
        if is_tracked(src):
            git("mv", "--", src, dst)
        else:
            (ROOT / src).rename(ROOT / dst)


def snapshot_history(plan: Plan) -> None:
    for rel in SNAPSHOTS:
        shown = git("show", f"HEAD:{rel}", check=False)
        if shown.returncode != 0:
            plan.say(f"  atlandı (HEAD'de yok): {rel}")
            continue
        stem = Path(rel).stem
        target = f"docs/archive/history/{stem}_{DATE}_full.md"
        plan.say(f"  {rel} -> {target}")
        if plan.apply:
            path = ROOT / target
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(shown.stdout, encoding="utf-8", newline="\n")
            git("add", "--", target)


def archive_docs(plan: Plan) -> list[str]:
    moved: list[str] = []
    for item in sorted((ROOT / "docs").iterdir()):
        if item.name in KEEP_DOCS:
            continue
        plan.move(f"docs/{item.name}", f"docs/archive/research/{item.name}")
        moved.append(item.name)
    plan.say(f"  docs: {len(moved)} öğe -> docs/archive/research/")
    return moved


def archive_evidence(plan: Plan) -> list[str]:
    moved: list[str] = []
    for item in sorted((ROOT / "evidence").iterdir()):
        if item.name in KEEP_EVIDENCE or not item.is_dir():
            continue
        plan.move(f"evidence/{item.name}", f"evidence/archive/{item.name}")
        moved.append(item.name)
    plan.say(f"  evidence: {len(moved)} klasör -> evidence/archive/")
    return moved


def write_evidence_index(plan: Plan) -> None:
    lines = [
        "# Kanıt dizini",
        "",
        "Aktif fazların kanıtı bu klasörde, eskiler `archive/` altındadır.",
        "Yeni kanıt: faz başına tek `<faz>/SONUC.md` (≤ 60 satır).",
        "",
        "## Aktif",
    ]
    for name in sorted(KEEP_EVIDENCE - {"archive"}):
        lines.append(f"- `{name}/`")
    lines += ["", "## Arşiv", "- `archive/` — P1.x ve önceki dilimlerin kanıtları (varsayılan olarak okunmaz)."]
    plan.say("  evidence/INDEX.md yazılacak")
    if plan.apply:
        (ROOT / "evidence/INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        git("add", "--", "evidence/INDEX.md")


def compact_matrix(plan: Plan) -> None:
    path = ROOT / "docs/OZELLIK_MATRISI.md"
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    first_section = next(i for i, l in enumerate(lines) if l.startswith("## "))
    head_idx = next(i for i, l in enumerate(lines) if l.startswith("| ID |"))
    end_idx = head_idx
    while end_idx < len(lines) and lines[end_idx].lstrip().startswith("|"):
        end_idx += 1
    ref_idx = next(i for i, l in enumerate(lines) if l.startswith("## Referanslar"))
    ref_end = next(
        (i for i in range(ref_idx + 1, len(lines)) if lines[i].startswith("## ")),
        len(lines),
    )

    def shorten(cell: str) -> str:
        cell = cell.strip()
        if len(cell) <= MATRIX_CELL_LIMIT:
            return cell
        cut = cell[:MATRIX_CELL_LIMIT]
        semi = cut.rfind(";")
        if semi > 60:
            cut = cut[:semi]
        else:
            cut = cut[: cut.rfind(" ")]
        return cut.rstrip(" ,;") + " …"

    table = []
    for line in lines[head_idx:end_idx]:
        line = line.strip()  # kaynakta bazı satırlar boşlukla başlıyor
        cells = line.split("|")
        if len(cells) == 7 and line.startswith("| F"):
            cells[5] = " " + shorten(cells[5]) + " "
            line = "|".join(cells)
        table.append(line)

    intro = [l for l in lines[:first_section]]
    note = [
        "## Kullanım",
        "",
        "Bu tablo kapsamın tek kaynağıdır. `Bugünkü durum` hücresi kısa durum tutar "
        "(PLAN / KISMEN / LOCAL / TESTNET); dilim günlüğü buraya yazılmaz. Hücreler "
        f"{MATRIX_CELL_LIMIT} karaktere kısaltıldı; önceki tam metin: "
        f"`docs/archive/history/OZELLIK_MATRISI_{DATE}_full.md`.",
        "",
        "## Matris",
        "",
    ]
    out = intro + note + table + [""] + lines[ref_idx:ref_end]
    result = "\n".join(out).rstrip("\n") + "\n"
    plan.say(
        f"  OZELLIK_MATRISI: {len(text.encode('utf-8'))} -> {len(result.encode('utf-8'))} bayt"
    )
    if plan.apply:
        path.write_text(result, encoding="utf-8", newline="\n")


def rewrite_paths(plan: Plan, docs_moved: list[str], evidence_moved: list[str]) -> None:
    replacements: list[tuple[re.Pattern[str], str]] = []
    for name in sorted(docs_moved, key=len, reverse=True):
        replacements.append(
            (
                re.compile(r"(?<![\w./-])docs/" + re.escape(name) + r"(?![\w-]|\.[\w])"),
                f"docs/archive/research/{name}",
            )
        )
    for name in sorted(evidence_moved, key=len, reverse=True):
        replacements.append(
            (
                re.compile(r"(?<![\w./-])evidence/" + re.escape(name) + r"(?![\w-]|\.[\w])"),
                f"evidence/archive/{name}",
            )
        )
    tracked = git("ls-files", "-z", "--", "*.md").stdout.split("\0")
    changed = 0
    for rel in filter(None, tracked):
        if rel.startswith(("docs/archive/", "evidence/archive/")) or rel in SNAPSHOTS:
            continue
        path = ROOT / rel
        if not path.is_file():
            # git mv sonrası eski yol yok; taşınmış dosyayı atla
            continue
        text = path.read_text(encoding="utf-8")
        new = text
        for pattern, repl in replacements:
            new = pattern.sub(repl, new)
        if new != text:
            changed += 1
            if plan.apply:
                path.write_text(new, encoding="utf-8", newline="\n")
    plan.say(f"  yol düzeltmesi: {changed} .md dosyası güncellenecek")


def fix_readme(plan: Plan) -> None:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    if README_OLD in text:
        plan.say("  README: bağımlılık cümlesi düzeltilecek")
        if plan.apply:
            path.write_text(text.replace(README_OLD, README_NEW), encoding="utf-8", newline="\n")
    else:
        plan.say("  README: eski cümle bulunamadı — 'Harici Python bağımlılığı yok' ifadesini elle düzelt")


def update_ignore(plan: Plan) -> None:
    path = ROOT / ".ignore"
    existing = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    wanted = ["docs/archive/", "evidence/archive/", "SHA256SUMS.txt"]
    missing = [w for w in wanted if w not in existing]
    plan.say(f"  .ignore: eklenecek {missing or 'yok'}")
    if plan.apply and missing:
        path.write_text("\n".join(existing + missing) + "\n", encoding="utf-8", newline="\n")


def report_dangling(docs_moved: list[str], evidence_moved: list[str]) -> None:
    names = docs_moved
    tracked = git("ls-files", "-z", "--", "*.md").stdout.split("\0")
    hits: list[str] = []
    for rel in filter(None, tracked):
        if rel.startswith(("docs/archive/", "evidence/archive/")) or rel in SNAPSHOTS:
            continue
        path = ROOT / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for name in names:
            if re.search(r"(?<![\w./-])" + re.escape(name), text):
                hits.append(f"{rel}: '{name}' bağımsız adla anılıyor")
    if hits:
        print("\nElle kontrol edilecek göreli bağlantılar:")
        for h in sorted(set(hits))[:40]:
            print("  -", h)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="değişiklikleri uygula (varsayılan: dry-run)")
    args = parser.parse_args()

    status = git("status", "--porcelain", "--untracked-files=no").stdout.strip()
    if args.apply and status:
        print("Çalışma ağacı temiz değil. Önce commit/stash yap:\n" + status, file=sys.stderr)
        return 1
    if not args.apply:
        print("DRY-RUN — hiçbir dosya değişmeyecek. Uygulamak için --apply ekle.\n")

    plan = Plan(args.apply)
    print("1) Geçmiş sürümlerin tam kopyası")
    snapshot_history(plan)
    print("2) docs/ arşivi")
    docs_moved = archive_docs(plan)
    print("3) evidence/ arşivi")
    evidence_moved = archive_evidence(plan)
    write_evidence_index(plan)
    print("4) Özellik matrisi sıkıştırma")
    compact_matrix(plan)
    print("5) Yol düzeltmeleri, README, .ignore")
    rewrite_paths(plan, docs_moved, evidence_moved)
    fix_readme(plan)
    update_ignore(plan)
    if args.apply:
        report_dangling(docs_moved, evidence_moved)
        print(
            "\nBitti. Sıradaki adımlar:\n"
            "  1) Yeni AGENTS/STATE/TASK/WORKFLOW/CLAUDE/GEMINI/OPENCODE, docs/YOL_HARITASI.md,\n"
            "     tools/check_workspace.py ve tests/test_doc_limits.py dosyalarını kökün üzerine kopyala\n"
            "  2) git add -A && python tools/release_manifest.py generate && git add SHA256SUMS.txt\n"
            "  3) uv run --frozen python tools/run_checks.py ve python tools/release_manifest.py"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
