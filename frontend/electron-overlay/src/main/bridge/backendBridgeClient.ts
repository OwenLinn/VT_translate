import { WebSocket } from "ws";
import type { BackendEvent, CommandMessage, CommandName } from "../../shared/backendBridgeTypes";
import { appendDebugLog } from "../debugLog";

export interface BackendBridgeClient {
  sendCommand: (command: CommandName, value?: string | boolean) => boolean;
  close: () => void;
}

function coerceMessageData(data: unknown): string {
  if (typeof data === "string") {
    return data;
  }
  if (data instanceof ArrayBuffer) {
    const decoder = new TextDecoder();
    return decoder.decode(new Uint8Array(data));
  }
  if (ArrayBuffer.isView(data)) {
    const decoder = new TextDecoder();
    return decoder.decode(new Uint8Array(data.buffer, data.byteOffset, data.byteLength));
  }
  return String(data);
}

export function createBackendBridgeClient(
  url: string,
  onEvent: (event: BackendEvent) => void,
  onConnectionChange: (connected: boolean, detail?: string) => void
): BackendBridgeClient {
  let socket: WebSocket | null = null;
  let closed = false;
  let reconnectTimer: NodeJS.Timeout | null = null;
  let reconnectAttempt = 0;

  const connect = (): void => {
    if (closed) {
      return;
    }
    reconnectAttempt += 1;
    try {
      socket = new WebSocket(url);
    } catch (error) {
      console.error(`[bridge] WebSocket constructor failed: ${String(error)}`);
      onConnectionChange(false, String(error));
      scheduleReconnect();
      return;
    }

    socket.addEventListener("open", () => {
      console.log("[bridge] connected to backend");
      appendDebugLog("bridge", "connected to backend");
      reconnectAttempt = 0;
      onConnectionChange(true);
    });
    socket.addEventListener("message", (message) => {
      let raw: string;
      try {
        raw = coerceMessageData(message.data);
      } catch (error) {
        console.error("[bridge] failed to read message data:", error);
        return;
      }
      try {
        const event = JSON.parse(raw) as BackendEvent;
        console.log(`[bridge] recv event: type=${event.type}`);
        appendDebugLog("bridge", `recv event type=${event.type}`);
        onEvent(event);
      } catch (error) {
        console.error(`[bridge] failed to parse event: ${String(error)}, raw=${raw.slice(0, 200)}`);
        appendDebugLog("bridge", `parse failed error=${String(error)} raw=${raw.slice(0, 200)}`);
      }
    });
    socket.addEventListener("close", (event) => {
      console.log(`[bridge] disconnected (code=${event.code})`);
      appendDebugLog("bridge", `disconnected code=${event.code}`);
      onConnectionChange(false);
      scheduleReconnect();
    });
    socket.addEventListener("error", (error) => {
      console.error("[bridge] WebSocket error:", error);
      appendDebugLog("bridge", `websocket error=${String(error)}`);
      onConnectionChange(false, "Backend WebSocket error");
    });
  };

  const scheduleReconnect = (): void => {
    if (closed || reconnectTimer) {
      return;
    }
      const delay = Math.min(1000 * Math.pow(2, Math.min(reconnectAttempt, 5)), 10000);
      console.log(`[bridge] reconnecting in ${delay}ms (attempt ${reconnectAttempt})`);
      appendDebugLog("bridge", `reconnecting delay=${delay}ms attempt=${reconnectAttempt}`);
      reconnectTimer = setTimeout(() => {
      reconnectTimer = null;
      connect();
    }, delay);
  };

  connect();

  return {
    sendCommand: (command, value) => {
      if (!socket || socket.readyState !== WebSocket.OPEN) {
        return false;
      }
      const message: CommandMessage = {
        type: "command",
        command,
        value,
        requestId: `${Date.now()}-${Math.random().toString(16).slice(2)}`
      };
      socket.send(JSON.stringify(message));
      appendDebugLog("bridge", `sent command=${command}`);
      return true;
    },
    close: () => {
      closed = true;
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
      socket?.close();
      socket = null;
    }
  };
}
