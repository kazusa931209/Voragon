import { appendAccessToken } from "./wsUrl";
import { buildAudioFrame } from "./frames";
import {
  buildControlMessage,
  errorCode,
  parseEnvelope,
  type MessageEnvelope,
} from "./messages";

export type ConnectionState =
  | "disconnected"
  | "connecting"
  | "ready"
  | "reconnecting"
  | "error";

export interface RealtimeClientCallbacks {
  onStateChange: (state: ConnectionState) => void;
  onMessage: (message: MessageEnvelope) => void;
  onSessionId: (sessionId: string) => void;
  onNotice: (text: string) => void;
}

const PING_INTERVAL_MS = 15_000;
const SESSION_RESUME_CODES = new Set(["SESSION_NOT_FOUND", "SESSION_EXPIRED"]);
const RECONNECT_BACKOFF_MS = [1000, 2000, 4000, 8000];

export interface RealtimeClientOptions {
  accessToken?: string | null;
}

export class RealtimeClient {
  private ws: WebSocket | null = null;
  private url: string;
  private accessToken: string | null;
  private language: string;
  private callbacks: RealtimeClientCallbacks;
  private sessionId: string | null = null;
  private lastSessionId: string | null = null;
  private reconnectWindowS = 30;
  private intentionalClose = false;
  private streaming = false;
  private pingTimer: ReturnType<typeof setInterval> | null = null;
  private seqNum = 0;
  private resumeAttempted = false;
  private reconnectInFlight: Promise<void> | null = null;
  private replacingSocket = false;
  private restoreStreamingAfterReconnect = false;
  /** Server closes the WebSocket after session.ended (e.g. audio.stop); do not auto-resume. */
  private suppressReconnectOnClose = false;

  constructor(
    url: string,
    language: string,
    callbacks: RealtimeClientCallbacks,
    options?: RealtimeClientOptions,
  ) {
    this.url = url;
    this.accessToken = options?.accessToken ?? null;
    this.language = language;
    this.callbacks = callbacks;
  }

  getSessionId(): string | null {
    return this.sessionId;
  }

  isStreaming(): boolean {
    return this.streaming;
  }

  /** True while reconnecting or waiting for session.started after an unexpected drop. */
  isRecovering(): boolean {
    if (this.intentionalClose) {
      return false;
    }
    if (this.reconnectInFlight !== null) {
      return true;
    }
    if (this.suppressReconnectOnClose) {
      return false;
    }
    return this.lastSessionId !== null && this.sessionId === null;
  }

  async connect(): Promise<void> {
    this.intentionalClose = false;
    this.resumeAttempted = false;
    await this.openSocket(false);
  }

  disconnect(): void {
    this.intentionalClose = true;
    this.reconnectInFlight = null;
    this.restoreStreamingAfterReconnect = false;
    this.stopPing();
    this.streaming = false;
    this.detachAndCloseWs();
    this.sessionId = null;
    this.lastSessionId = null;
    this.notifySessionId(null);
    this.callbacks.onStateChange("disconnected");
  }

  async startAudio(): Promise<void> {
    if (!this.ws || !this.sessionId) {
      throw new Error("Not connected");
    }
    this.ws.send(
      buildControlMessage("audio.start", this.sessionId, { language: this.language }),
    );
    this.streaming = true;
    this.stopPing();
    this.seqNum = 0;
  }

  async stopAudio(): Promise<void> {
    if (!this.ws || !this.sessionId) {
      return;
    }
    this.streaming = false;
    this.restoreStreamingAfterReconnect = false;
    this.suppressReconnectOnClose = true;
    this.ws.send(buildControlMessage("audio.stop", this.sessionId, {}));
  }

  sendPcmFrame(pcm: Uint8Array): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN || !this.streaming) {
      return;
    }
    this.ws.send(buildAudioFrame(pcm, this.seqNum));
    this.seqNum += 1;
  }

  private detachAndCloseWs(): void {
    const ws = this.ws;
    this.ws = null;
    if (!ws) {
      return;
    }
    this.replacingSocket = true;
    ws.onclose = null;
    ws.onerror = null;
    ws.onmessage = null;
    try {
      ws.close();
    } catch {
      /* ignore */
    }
    this.replacingSocket = false;
  }

  private async openSocket(isReconnect: boolean): Promise<void> {
    this.resumeAttempted = false;
    this.detachAndCloseWs();
    this.callbacks.onStateChange(isReconnect ? "reconnecting" : "connecting");

    try {
      await new Promise<void>((resolve, reject) => {
        const connectUrl =
          this.accessToken != null && this.accessToken !== ""
            ? appendAccessToken(this.url, this.accessToken)
            : this.url;
        const ws = new WebSocket(connectUrl);
        ws.binaryType = "arraybuffer";
        this.ws = ws;

        ws.onopen = () => {
          resolve();
        };

        ws.onerror = () => {
          reject(new Error("WebSocket connection failed"));
        };

        ws.onclose = () => {
          this.stopPing();
          if (this.replacingSocket || this.intentionalClose) {
            return;
          }
          if (this.suppressReconnectOnClose) {
            this.suppressReconnectOnClose = false;
            this.streaming = false;
            this.sessionId = null;
            this.lastSessionId = null;
            this.notifySessionId(null);
            this.callbacks.onStateChange("disconnected");
            return;
          }
          const wasStreaming = this.streaming;
          this.streaming = false;
          if (wasStreaming) {
            this.restoreStreamingAfterReconnect = true;
          }
          this.sessionId = null;
          this.notifySessionId(null);
          if (this.lastSessionId) {
            void this.scheduleReconnect();
          } else {
            this.callbacks.onStateChange("disconnected");
          }
        };

        ws.onmessage = (event) => {
          if (typeof event.data === "string") {
            this.handleJsonMessage(event.data);
          }
        };
      });
    } catch (err) {
      if (!isReconnect) {
        this.callbacks.onStateChange("error");
      }
      throw err;
    }
  }

  private scheduleReconnect(): void {
    if (this.intentionalClose || !this.lastSessionId) {
      return;
    }
    if (this.reconnectInFlight) {
      return;
    }
    this.reconnectInFlight = this.tryReconnect().finally(() => {
      this.reconnectInFlight = null;
    });
  }

  private handleJsonMessage(raw: string): void {
    let message: MessageEnvelope;
    try {
      message = parseEnvelope(raw);
    } catch {
      return;
    }

    this.callbacks.onMessage(message);

    switch (message.type) {
      case "session.started": {
        const reconnectWindow = message.payload.reconnect_window_s;
        if (typeof reconnectWindow === "number") {
          this.reconnectWindowS = reconnectWindow;
        }
        const newId = message.session_id;
        if (
          !this.resumeAttempted &&
          this.lastSessionId &&
          this.lastSessionId !== newId &&
          this.ws
        ) {
          this.resumeAttempted = true;
          this.ws.send(buildControlMessage("session.resume", this.lastSessionId, {}));
          return;
        }
        void this.onSessionReady(newId);
        break;
      }
      case "error": {
        const code = errorCode(message);
        if (SESSION_RESUME_CODES.has(code)) {
          this.callbacks.onNotice(`Session resume failed (${code}); starting fresh.`);
          void this.onSessionReady(message.session_id);
        }
        break;
      }
      case "session.ended": {
        this.streaming = false;
        this.restoreStreamingAfterReconnect = false;
        this.suppressReconnectOnClose = true;
        this.sessionId = null;
        this.lastSessionId = null;
        this.notifySessionId(null);
        break;
      }
      case "pong":
        break;
      default:
        break;
    }
  }

  private async onSessionReady(sessionId: string): Promise<void> {
    this.sessionId = sessionId;
    this.lastSessionId = sessionId;
    this.notifySessionId(sessionId);
    this.callbacks.onStateChange("ready");

    if (this.restoreStreamingAfterReconnect) {
      this.restoreStreamingAfterReconnect = false;
      try {
        await this.startAudio();
      } catch {
        this.callbacks.onNotice("Reconnected but could not restart audio streaming.");
      }
    }
    if (!this.streaming) {
      this.startPing();
    }
  }

  private async tryReconnect(): Promise<void> {
    const previous = this.lastSessionId;
    if (!previous || this.intentionalClose) {
      this.callbacks.onStateChange("disconnected");
      return;
    }
    this.callbacks.onNotice("Reconnecting…");
    this.resumeAttempted = false;
    const deadline = Date.now() + this.reconnectWindowS * 1000;
    let backoffIndex = 0;

    while (Date.now() < deadline && !this.intentionalClose) {
      this.callbacks.onStateChange("reconnecting");
      try {
        await this.openSocket(true);
        return;
      } catch {
        const waitMs = RECONNECT_BACKOFF_MS[Math.min(backoffIndex, RECONNECT_BACKOFF_MS.length - 1)];
        backoffIndex += 1;
        await sleep(waitMs);
      }
    }
    this.callbacks.onStateChange("error");
    this.callbacks.onNotice("Reconnection failed.");
  }

  private startPing(): void {
    this.stopPing();
    if (!this.ws || this.streaming || !this.sessionId) {
      return;
    }
    this.pingTimer = setInterval(() => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN || this.streaming) {
        return;
      }
      if (!this.sessionId) {
        return;
      }
      this.ws.send(buildControlMessage("ping", this.sessionId, {}));
    }, PING_INTERVAL_MS);
  }

  private stopPing(): void {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }

  private notifySessionId(sessionId: string | null): void {
    this.callbacks.onSessionId(sessionId ?? "");
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
