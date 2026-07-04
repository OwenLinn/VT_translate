import type { BrowserWindow } from "electron";
import type { OverlayBounds, OverlayMode } from "../../shared/overlayIpcTypes";
import { createOverlayBrowserWindow } from "./createOverlayWindow";

export function createSettingsIconWindow(mode: OverlayMode, bounds: OverlayBounds): BrowserWindow {
  return createOverlayBrowserWindow({
    type: "settings-icon",
    mode,
    bounds,
    focusable: true,
    resizable: false,
    show: true
  });
}
