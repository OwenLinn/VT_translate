import { app, BrowserWindow } from "electron";
import { createOverlayWindow } from "./window";
import { registerLegacyOverlayIpc, registerOverlayManagerIpc } from "./ipc";
import type { OverlayMode, OverlayWindowMode } from "../shared/overlayIpcTypes";
import { createBackendBridgeClient, type BackendBridgeClient } from "./bridge/backendBridgeClient";
import { OverlayWindowManager } from "./windows/overlayWindowManager";

let overlayWindow: BrowserWindow | null = null;
let overlayWindowManager: OverlayWindowManager | null = null;
let backendBridgeClient: BackendBridgeClient | null = null;

const overlayMode: OverlayMode = process.env.OVERLAY_MODE === "tuning" ? "tuning" : "mock";
const overlayWindowMode: OverlayWindowMode =
  process.env.OVERLAY_WINDOW_MODE === "single_legacy" ? "single_legacy" : "multi";
const bridgeUrl = process.env.OVERLAY_BRIDGE_URL ?? "ws://127.0.0.1:8765";
const bridgeMode = process.env.OVERLAY_BRIDGE_MODE === "live";

app.whenReady().then(() => {
  if (overlayWindowMode === "single_legacy") {
    overlayWindow = createOverlayWindow(overlayMode);
    registerLegacyOverlayIpc(() => overlayWindow);
  } else {
    createManagedOverlay();
    registerOverlayManagerIpc(overlayWindowManager!);
  }

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      if (overlayWindowMode === "single_legacy") {
        overlayWindow = createOverlayWindow(overlayMode);
      } else {
        createManagedOverlay();
      }
    }
  });
});

app.on("window-all-closed", () => {
  backendBridgeClient?.close();
  backendBridgeClient = null;
  overlayWindowManager?.destroy();
  overlayWindowManager = null;
  if (process.platform !== "darwin") {
    app.quit();
  }
});

function createManagedOverlay(): void {
  backendBridgeClient?.close();
  backendBridgeClient = null;
  overlayWindowManager = new OverlayWindowManager(overlayMode, !bridgeMode);
  overlayWindowManager.createAll();
  if (!bridgeMode) {
    return;
  }
  backendBridgeClient = createBackendBridgeClient(
    bridgeUrl,
    (event) => overlayWindowManager?.applyBackendEvent(event),
    (connected, detail) => overlayWindowManager?.setBackendConnected(connected, detail)
  );
  overlayWindowManager.setBackendCommandSender((command, value) =>
    backendBridgeClient?.sendCommand(command, value) ?? false
  );
}
