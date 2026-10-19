/** Append JWT for browser WebSocket clients (no Authorization header support). */
export function appendAccessToken(wsUrl: string, accessToken: string): string {
  const url = new URL(wsUrl);
  url.searchParams.set("access_token", accessToken);
  return url.toString();
}
