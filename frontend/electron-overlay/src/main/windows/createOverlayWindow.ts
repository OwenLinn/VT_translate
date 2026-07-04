import { join } from "node:path";
import { BrowserWindow } from "electron";
import type { OverlayBounds, OverlayMode, OverlayWindowType } from "../../shared/overlayIpcTypes";

export interface CreateOverlayWindowOptions {
  type: OverlayWindowType;
  mode: OverlayMode;
  bounds: OverlayBounds;
  focusable: boolean;
  show?: boolean;
  resizable?: boolean;
}

export function createOverlayBrowserWindow(options: CreateOverlayWindowOptions): BrowserWindow {
  const win = new BrowserWindow({
    ...options.bounds,
    minWidth: Math.min(options.bounds.width, 120),
    minHeight: Math.min(options.bounds.height, 72),
    transparent: true,
    backgroundColor: "#00000000",
    frame: false,
    resizable: options.resizable ?? false,
    movable: true,
    focusable: options.focusable,
    alwaysOnTop: true,
    skipTaskbar: true,
    hasShadow: false,
    title: `YT Live Translator - ${options.type}`,
    show: options.show ?? true,
    webPreferences: {
      preload: join(__dirname, "../preload/preload.cjs"),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      devTools: true
    }
  });

  win.setAlwaysOnTop(true, "screen-saver");
  win.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });

  const params = new URLSearchParams({
    mode: options.mode,
    window: options.type
  });
  if (process.env.ELECTRON_RENDERER_URL) {
    win.loadURL(`${process.env.ELECTRON_RENDERER_URL}?${params.toString()}`);
  } else {
    win.loadFile(join(__dirname, "../renderer/index.html"), {
      query: Object.fromEntries(params.entries())
    });
  }

  return win;
}
