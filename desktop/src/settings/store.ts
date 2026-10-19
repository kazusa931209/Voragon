import { LazyStore } from "@tauri-apps/plugin-store";

export const DEFAULT_BACKEND_URL = "ws://localhost:8000/v1/realtime";

export interface AppSettings {
  backendUrl: string;
  authTokenUrl: string;
  authMintApiKey: string;
  inputDeviceIndex: number | null;
  language: string;
}

const defaultSettings: AppSettings = {
  backendUrl: DEFAULT_BACKEND_URL,
  authTokenUrl: "",
  authMintApiKey: "",
  inputDeviceIndex: null,
  language: "en",
};

let store: LazyStore | null = null;

async function getStore(): Promise<LazyStore> {
  if (!store) {
    store = new LazyStore("settings.json");
  }
  return store;
}

export async function loadSettings(): Promise<AppSettings> {
  const s = await getStore();
  const backendUrl = (await s.get<string>("backendUrl")) ?? defaultSettings.backendUrl;
  const authTokenUrl = (await s.get<string>("authTokenUrl")) ?? defaultSettings.authTokenUrl;
  const authMintApiKey =
    (await s.get<string>("authMintApiKey")) ?? defaultSettings.authMintApiKey;
  const inputDeviceIndex = (await s.get<number | null>("inputDeviceIndex")) ?? null;
  const language = (await s.get<string>("language")) ?? defaultSettings.language;
  return { backendUrl, authTokenUrl, authMintApiKey, inputDeviceIndex, language };
}

export async function saveSettings(settings: AppSettings): Promise<void> {
  const s = await getStore();
  await s.set("backendUrl", settings.backendUrl);
  await s.set("authTokenUrl", settings.authTokenUrl);
  await s.set("authMintApiKey", settings.authMintApiKey);
  await s.set("inputDeviceIndex", settings.inputDeviceIndex);
  await s.set("language", settings.language);
  await s.save();
}
