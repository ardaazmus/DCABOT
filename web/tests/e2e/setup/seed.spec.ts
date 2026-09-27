import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { expect, test, type APIRequestContext } from "@playwright/test";

// e2e tohumlama: chromium projesinden önce koşar (project dependencies).
// API (8771) + web (3771) çalışır durumdadır. Her adım gerçek uçlarla
// yapılır; başarısızlık yüksek sesle düşer, testler atlanmaz.
test.setTimeout(720_000);

const API = "http://127.0.0.1:8771";
const DATASET_ID = "binance-spot-klines-v1-btcusdt-1h-2025-01-01";
const PROFILE_ID = "historical_demo_btcusdt_1h_v1";

type JobResponse = {
  job: { job_id: string; status: string; error_code: string | null; error_message: string | null };
};

type JobStatus = {
  status: string;
  error_code: string | null;
  error_message: string | null;
};

async function waitForDownload(request: APIRequestContext, jobId: string): Promise<void> {
  // Canlı Binance yukarı-akımı; bütçe cömerttir, SUCCEEDED erken çıkar.
  for (let attempt = 0; attempt < 300; attempt++) {
    const response = await request.get(`${API}/api/dataset-downloads/${jobId}`);
    if (!response.ok()) {
      throw new Error(`Tohumlama durdu: download job okunamadı (HTTP ${response.status()}).`);
    }
    const job = (await response.json()) as JobStatus;
    if (job.status === "SUCCEEDED") return;
    if (job.status === "FAILED" || job.status === "CANCELLED") {
      throw new Error(
        `Tohumlama durdu: dataset indirilemedi (${job.error_code ?? "?"}) ${job.error_message ?? ""}`.trim(),
      );
    }
    await new Promise((done) => setTimeout(done, 2000));
  }
  throw new Error("Tohumlama durdu: dataset indirme 10 dk'da bitmedi.");
}

test("tohum: dataset indir + geçmiş koşu kaydet", async ({ request }) => {
  // 1. Kayıtlı dataset indirilir → katalogda VERIFIED olur.
  const start = await request.post(`${API}/api/dataset-downloads`, {
    data: { dataset_id: DATASET_ID },
  });
  if (start.status() !== 202) {
    throw new Error(
      `Tohumlama durdu: download başlayamadı (HTTP ${start.status()}): ${(await start.text()).slice(0, 200)}`,
    );
  }
  const started = (await start.json()) as JobResponse;
  await waitForDownload(request, started.job.job_id);

  const catalog = await request.get(`${API}/api/datasets`);
  if (!catalog.ok()) throw new Error("Tohumlama durdu: katalog okunamadı.");
  const entries = ((await catalog.json()) as { datasets: { dataset_id: string; status: string }[] }).datasets;
  const entry = entries.find((item) => item.dataset_id === DATASET_ID);
  if (entry?.status !== "VERIFIED") {
    throw new Error(`Tohumlama durdu: dataset VERIFIED değil (${entry?.status ?? "yok"}).`);
  }

  // 2. Geçmiş koşu simüle + kaydet → historical_runs.sqlite3 oluşur.
  const plan = await request.get(
    `${API}/api/datasets/${DATASET_ID}/run-plan?profile_id=${PROFILE_ID}`,
  );
  if (!plan.ok()) {
    throw new Error(`Tohumlama durdu: run-plan alınamadı (HTTP ${plan.status()}).`);
  }
  const planBody = (await plan.json()) as {
    config: { config_hash: string };
    dataset: { artifact: { sha256: string } };
  };
  const simulate = await request.post(`${API}/api/historical-runs/simulate`, {
    data: {
      dataset_id: DATASET_ID,
      profile_id: PROFILE_ID,
      artifact_sha256: planBody.dataset.artifact.sha256,
      config_hash: planBody.config.config_hash,
      execution_mode: "historical_ohlcv_v1",
    },
  });
  if (!simulate.ok()) {
    throw new Error(
      `Tohumlama durdu: simulate başarısız (HTTP ${simulate.status()}): ${(await simulate.text()).slice(0, 200)}`,
    );
  }
  const executionId = ((await simulate.json()) as { execution_id: string }).execution_id;
  const save = await request.post(`${API}/api/historical-runs`, {
    data: { execution_id: executionId },
  });
  if (save.status() !== 201) {
    throw new Error(
      `Tohumlama durdu: koşu kaydedilemedi (HTTP ${save.status()}): ${(await save.text()).slice(0, 200)}`,
    );
  }

  // Koşuya özel veri klasörü config'den env ile gelir.
  const e2eData = process.env.DCABOT_E2E_DATA_DIR;
  expect(e2eData, "Tohumlama durdu: DCABOT_E2E_DATA_DIR tanımsız.").toBeTruthy();
  const sqlitePath = resolve(e2eData as string, "historical_runs.sqlite3");
  expect(existsSync(sqlitePath), "Tohumlama durdu: historical_runs.sqlite3 oluşmadı.").toBe(true);
});
