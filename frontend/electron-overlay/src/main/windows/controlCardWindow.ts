import type { BrowserWindow } from "electron";
import type { OverlayBounds, OverlayMode } from "../../shared/overlayIpcTypes";
import { createOverlayBrowserWindow } from "./createOverlayWindow";

export function createControlCardWindow(mode: OverlayMode, bounds: OverlayBounds): BrowserWindow {
  return createOverlayBrowserWindow({
    type: "control-card",
    mode,
    bounds,
    focusable: true,
    resizable: false,
    show: false
  });
}
