export interface AccessTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export async function fetchAccessToken(
  tokenUrl: string,
  mintApiKey: string,
): Promise<string> {
  const response = await fetch(tokenUrl, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-api-key": mintApiKey,
    },
    body: "{}",
  });
  if (!response.ok) {
    throw new Error(`Token request failed (${response.status})`);
  }
  const data = (await response.json()) as AccessTokenResponse;
  if (!data.access_token) {
    throw new Error("Token response missing access_token");
  }
  return data.access_token;
}
