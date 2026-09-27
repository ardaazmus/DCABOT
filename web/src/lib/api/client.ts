import { z } from "zod";

import {
  legacyErrorSchema,
  problemSchema,
  type LegacyError,
  type ProblemDetails,
} from "./schemas";

/** Sunucu yanıtı zod şemasına uymadığında fırlatılır. Sessiz geçiş yok. */
export class ApiContractError extends Error {
  readonly path: string;
  readonly issues: z.ZodIssue[];

  constructor(path: string, issues: z.ZodIssue[]) {
    super(`API sözleşme ihlali: ${path}`);
    this.name = "ApiContractError";
    this.path = path;
    this.issues = issues;
  }
}

/**
 * HTTP durumu 2xx değilse fırlatılır. İki hata biçimi ayrıştırılır:
 * `application/problem+json` → `problem`, eski `{"error":{...}}`
 * biçimi → `legacy`. Arayüzün göstereceği metin (`message`) backend'in
 * `detail`/`message` alanıdır; ham istisna metni arayüze çıkmaz.
 */
export class ApiHttpError extends Error {
  readonly path: string;
  readonly status: number;
  readonly problem?: ProblemDetails;
  readonly legacy?: LegacyError;

  constructor(
    path: string,
    status: number,
    problem?: ProblemDetails,
    legacy?: LegacyError,
  ) {
    super(
      problem?.detail ??
        legacy?.error.message ??
        `API HTTP hatası: ${path} -> ${status}`,
    );
    this.name = "ApiHttpError";
    this.path = path;
    this.status = status;
    this.problem = problem;
    this.legacy = legacy;
  }
}

/** Ağ isteği yanıtsız kaldığında fırlatılır (backend kapalı, DNS, CORS…). */
export class ApiNetworkError extends Error {
  readonly path: string;

  constructor(path: string, cause: unknown) {
    super(`API ağ hatası: ${path}`);
    this.name = "ApiNetworkError";
    this.path = path;
    this.cause = cause;
  }
}

async function readJson(path: string, response: Response): Promise<unknown> {
  try {
    return (await response.json()) as unknown;
  } catch {
    throw new ApiContractError(path, [
      {
        code: "custom",
        message: "Yanıt JSON olarak okunamadı",
        path: [],
      } satisfies z.ZodIssue,
    ]);
  }
}

/**
 * Hata gövdesini iki biçimde de dener: önce `application/problem+json`,
 * sonra eski `{"error":{...}}` biçimi. İkisi de tutmazsa ya da gövde
 * bozuksa `undefined` döner; çağrı zaten `ApiHttpError` ile
 * sonuçlanacağı için burada ek hata fırlatılmaz.
 */
async function readError(response: Response): Promise<{
  problem?: ProblemDetails;
  legacy?: LegacyError;
}> {
  const contentType = response.headers.get("content-type") ?? "";
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    return {};
  }
  if (contentType.includes("application/problem+json")) {
    const parsed = problemSchema.safeParse(body);
    return parsed.success ? { problem: parsed.data } : {};
  }
  const parsed = legacyErrorSchema.safeParse(body);
  return parsed.success ? { legacy: parsed.data } : {};
}

async function request<T>(
  path: string,
  schema: z.ZodType<T>,
  init?: RequestInit,
): Promise<T> {
  // İptal edilen istek (AbortController) yanıtsız kalır; ağ hatası sayılmaz.
  if (init?.signal?.aborted === true) {
    throw new DOMException("İstek iptal edildi", "AbortError");
  }
  let response: Response;
  try {
    response = await fetch(path, init);
  } catch (error) {
    // Kullanıcı iptali ağ hatası değildir; aynen yukarı taşınır.
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiNetworkError(path, error);
  }
  if (!response.ok) {
    const { problem, legacy } = await readError(response);
    throw new ApiHttpError(path, response.status, problem, legacy);
  }
  const body: unknown = await readJson(path, response);
  const parsed = schema.safeParse(body);
  if (!parsed.success) {
    throw new ApiContractError(path, parsed.error.issues);
  }
  return parsed.data;
}

/** Tarayıcı her zaman `/api/...` yoluna gider (Next rewrite backend'e proxy'ler). */
export function apiGet<T>(path: string, schema: z.ZodType<T>): Promise<T> {
  return request(path, schema, { method: "GET" });
}

export function apiDelete<T>(path: string, schema: z.ZodType<T>): Promise<T> {
  return request(path, schema, { method: "DELETE" });
}

export function apiPost<T>(
  path: string,
  body: unknown,
  schema: z.ZodType<T>,
  options?: { signal?: AbortSignal },
): Promise<T> {
  return request(
    path,
    schema,
    {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
      signal: options?.signal,
    },
  );
}
