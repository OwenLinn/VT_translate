import type { BrowserWindow } from "electron";
import type { OverlayBounds, OverlayMode } from "../../shared/overlayIpcTypes";
import { createOverlayBrowserWindow } from "./createOverlayWindow";

export function createSubtitleWindow(mode: OverlayMode, bounds: OverlayBounds): BrowserWindow {
  return createOverlayBrowserWindow({
    type: "subtitle",
    mode,
    bounds,
    focusable: false,
    resizable: false,
    show: true
  });
}
