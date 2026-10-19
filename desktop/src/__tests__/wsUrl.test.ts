import { describe, expect, it } from "vitest";
import { appendAccessToken } from "../api/wsUrl";

describe("appendAccessToken", () => {
  it("adds access_token query param", () => {
    const url = appendAccessToken("wss://example.com/v1/realtime", "abc.def");
    expect(url).toBe("wss://example.com/v1/realtime?access_token=abc.def");
  });

  it("preserves existing query params", () => {
    const url = appendAccessToken("wss://example.com/v1/realtime?foo=1", "tok");
    expect(url).toContain("foo=1");
    expect(url).toContain("access_token=tok");
  });
});
