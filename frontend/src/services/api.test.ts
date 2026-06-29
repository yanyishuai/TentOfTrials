import { afterEach, describe, expect, it, vi } from "vitest";

import { get, isApiError } from "./api";

function jsonResponse(body: unknown, init: ResponseInit & { headers?: Record<string, string> }) {
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  return new Response(JSON.stringify(body), { ...init, headers });
}

describe("api error handling", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    localStorage.clear();
  });

  it("returns successful 2xx responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({ ok: true }, { status: 200, headers: { "X-Request-ID": "req-200" } }),
      ),
    );

    const result = await get<{ ok: boolean }>("/health");
    expect(result.status).toBe(200);
    expect(result.data.ok).toBe(true);
    expect(result.requestId).toBe("req-200");
  });

  it("rejects 401 JSON errors with structured ApiError fields", async () => {
    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(
          {
            error: {
              message: "Unauthorized",
              details: { reason: "token_expired" },
              path: "/profile",
            },
            requestId: "req-401",
          },
          { status: 401 },
        ),
      ),
    );

    await expect(get("/profile")).rejects.toMatchObject({
      code: 401,
      message: "Unauthorized",
      requestId: "req-401",
      path: "/profile",
      details: { reason: "token_expired" },
    });
    expect(warnSpy).toHaveBeenCalled();
    warnSpy.mockRestore();
  });

  it("rejects 429 rate-limit JSON errors", async () => {
    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({ message: "Too many requests", requestId: "req-429" }, { status: 429 }),
      ),
    );

    const error = await get("/orders").catch((value) => value);
    expect(isApiError(error)).toBe(true);
    expect(error).toMatchObject({ code: 429, message: "Too many requests", requestId: "req-429" });
    expect(warnSpy).toHaveBeenCalled();
    warnSpy.mockRestore();
  });

  it("rejects 500 text errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response("upstream unavailable", {
          status: 500,
          statusText: "Internal Server Error",
          headers: { "Content-Type": "text/plain", "X-Request-ID": "req-500" },
        }),
      ),
    );

    await expect(get("/reports")).rejects.toMatchObject({
      code: 500,
      message: "upstream unavailable",
      requestId: "req-500",
    });
  });

  it("maps aborted requests to timeout ApiError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(
        Object.assign(new Error("The operation was aborted."), { name: "AbortError" }),
      ),
    );

    await expect(get("/slow", undefined, { retries: 0 })).rejects.toMatchObject({
      code: 408,
      message: "Request timed out",
    });
  });
});
