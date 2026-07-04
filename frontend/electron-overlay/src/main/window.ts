import { join } from "node:path";
import { BrowserWindow, screen } from "electron";

export type OverlayMode = "mock" | "tuning";

export function createOverlayWindow(mode: OverlayMode): BrowserWindow {
  const display = screen.getPrimaryDisplay();
  const width = mode === "tuning" ? 1120 : 920;
  const height = mode === "tuning" ? 720 : 220;
  const bounds = display.workArea;

  const win = new BrowserWindow({
    width,
    height,
    x: Math.max(bounds.x + 24, bounds.x + Math.floor((bounds.width - width) / 2)),
    y: bounds.y + 72,
    minWidth: 680,
    minHeight: 160,
    transparent: true,
    backgroundColor: "#00000000",
    frame: false,
    resizable: true,
    movable: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    hasShadow: false,
    title: "YouTube Live Translator Overlay",
    webPreferences: {
      preload: join(__dirname, "../preload/preload.js"),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      devTools: true
    }
  });

  win.setAlwaysOnTop(true, "screen-saver");
  win.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });

  const query = `?mode=${encodeURIComponent(mode)}`;
  if (process.env.ELECTRON_RENDERER_URL) {
    win.loadURL(`${process.env.ELECTRON_RENDERER_URL}${query}`);
  } else {
    win.loadFile(join(__dirname, "../renderer/index.html"), { query: { mode } });
  }

  return win;
}
