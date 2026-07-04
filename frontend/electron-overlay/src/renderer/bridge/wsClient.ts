import type { BackendEvent, CommandMessage } from "./messageTypes";

export const BRIDGE_URL = "ws://127.0.0.1:8765";

export interface OverlaySocket {
  sendCommand: (message: CommandMessage) => boolean;
  close: () => void;
}

export function connectOverlaySocket(onEvent: (event: BackendEvent) => void): OverlaySocket {
  let socket: WebSocket | null = null;

  try {
    socket = new WebSocket(BRIDGE_URL);
  } catch {
    onEvent({ type: "status", status: "idle", backendConnected: false });
  }

  if (socket) {
    socket.addEventListener("open", () => {
      onEvent({ type: "status", status: "running", backendConnected: true });
    });
    socket.addEventListener("close", () => {
      onEvent({ type: "status", status: "idle", backendConnected: false });
    });
    socket.addEventListener("error", () => {
      onEvent({ type: "status", status: "error", backendConnected: false, detail: "WebSocket error" });
    });
    socket.addEventListener("message", (message) => {
      try {
        onEvent(JSON.parse(String(message.data)) as BackendEvent);
      } catch {
        onEvent({
          type: "status",
          status: "error",
          backendConnected: false,
          detail: "Invalid bridge message"
        });
      }
    });
  }

  return {
    sendCommand: (message) => {
      if (!socket || socket.readyState !== WebSocket.OPEN) {
        return false;
      }
      socket.send(JSON.stringify(message));
      return true;
    },
    close: () => socket?.close()
  };
}

export function command(command: CommandMessage["command"], value?: string | boolean): CommandMessage {
  return {
    type: "command",
    command,
    value,
    requestId: `${Date.now()}-${Math.random().toString(16).slice(2)}`
  };
}
