import { NextRequest } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

/**
 * SSE geçişi: Next rewrite proxy'si sonsuz yanıtları tamponladığı
 * için akış bu Route Handler'dan geçirilir (ReadableStream aynen
 * istemciye akar). İmleç ve Last-Event-ID yukarı iletilir.
 */
export async function GET(request: NextRequest) {
  const apiUrl = process.env.DCABOT_API_URL ?? "http://127.0.0.1:8770";
  const incoming = new URL(request.url);
  const headers: Record<string, string> = { Accept: "text/event-stream" };
  const resume = request.headers.get("last-event-id");
  if (resume !== null) {
    headers["last-event-id"] = resume;
  }
  const upstream = await fetch(`${apiUrl}/api/stream${incoming.search}`, {
    headers,
    signal: request.signal,
  });
  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
