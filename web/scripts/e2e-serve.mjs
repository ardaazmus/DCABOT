import { spawnSync } from "node:child_process";

// e2e web sunucusu: AYRI dist klasörüne üretim derlemesi + next start.
// `next dev` kullanılmaz; dev sunucusu (3770) açıkken bile çakışmaz.
// Rewrite hedefi build anında gömülür → derleme e2e API'sine (8771) yapılır.
process.env.NEXT_DIST_DIR = ".next-e2e";
process.env.DCABOT_API_URL = "http://127.0.0.1:8771";

const build = spawnSync("npx", ["next", "build"], {
  stdio: "inherit",
  shell: process.platform === "win32",
});
if (build.status !== 0) {
  console.error(`e2e: next build düştü (çıkış ${build.status ?? "?"}).`);
  process.exit(build.status ?? 1);
}

const start = spawnSync("npx", ["next", "start", "--port", "3771"], {
  stdio: "inherit",
  shell: process.platform === "win32",
});
process.exit(start.status ?? 1);
