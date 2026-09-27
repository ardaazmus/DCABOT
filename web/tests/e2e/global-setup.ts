import { mkdirSync, readdirSync, rmSync } from "node:fs";
import { join } from "node:path";

/**
 * e2e yalıtımı: her koşu kendi boş veri klasörüyle başlar
 * (`DCABOT_E2E_DATA_DIR`, config üretir; worker'lara env ile geçer).
 * Önceki koşuların klasörleri silinir (şu anki hariç); kilitli olan
 * (çalışan başka bir koşu) atlanır. Gerçek `data/` klasörüne yazılmaz.
 */
export default function globalSetup() {
  const e2eData = process.env.DCABOT_E2E_DATA_DIR;
  if (!e2eData) {
    throw new Error("Tohumlama durdu: DCABOT_E2E_DATA_DIR tanımsız (config üretmeliydi).");
  }
  mkdirSync(e2eData, { recursive: true });
  const webDir = join(e2eData, "..");
  for (const entry of readdirSync(webDir)) {
    if (!entry.startsWith(".e2e-data-") || join(webDir, entry) === e2eData) continue;
    try {
      rmSync(join(webDir, entry), { recursive: true, force: true });
    } catch {
      // Kilitli klasör başka bir koşunundur; atlanır, koşu düşmez.
    }
  }
}
