/**
 * SSE streaming proxy for the analysis stream endpoint.
 *
 * Next.js rewrites() buffer SSE responses — this Route Handler bypasses that
 * by piping the upstream ReadableStream directly to the client with the
 * correct no-cache / no-transform headers required for true server-sent events.
 */

export const dynamic = "force-dynamic";

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;

  let upstream: Response;
  try {
    upstream = await fetch(`${BACKEND}/api/analyze/${id}/stream`, {
      headers: {
        Accept: "text/event-stream",
        "Cache-Control": "no-cache",
      },
    });
  } catch {
    return new Response("Failed to connect to analysis service", { status: 502 });
  }

  if (!upstream.ok || !upstream.body) {
    return new Response("Analysis stream unavailable", { status: upstream.status });
  }

  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      "X-Accel-Buffering": "no",
      Connection: "keep-alive",
    },
  });
}
