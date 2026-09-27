import type { NextConfig } from "next";

const DCABOT_API_URL = process.env.DCABOT_API_URL ?? "http://127.0.0.1:8770";

const nextConfig: NextConfig = {
  // e2e üretim derlemesi ayrı klasöre (dev .next'ine dokunulmaz).
  distDir: process.env.NEXT_DIST_DIR ?? ".next",
  // Yerel convention 127.0.0.1; Next 16 dev kaynaklarını varsayılan engeller.
  allowedDevOrigins: ["127.0.0.1"],
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${DCABOT_API_URL}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
