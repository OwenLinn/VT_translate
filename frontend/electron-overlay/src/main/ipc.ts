import { BrowserWindow, clipboard, ipcMain } from "electron";
import type { OpenPopoverPayload, SettingSelectedPayload } from "../shared/overlayIpcTypes";
import { OVERLAY_IPC } from "../shared/overlayIpcTypes";
import type { OverlayWindowManager } from "./windows/overlayWindowManager";

type WindowGetter = () => BrowserWindow | null;

export function registerLegacyOverlayIpc(getWindow: WindowGetter): void {
  ipcMain.handle(OVERLAY_IPC.setInteractive, (_event, interactive: boolean) => {
    const win = getWindow();
    if (!win) {
      return false;
    }
    win.setIgnoreMouseEvents(!interactive, { forward: true });
    return true;
  });

  ipcMain.handle(OVERLAY_IPC.copyText, (_event, text: string) => {
    clipboard.writeText(text);
    return true;
  });
}

export function registerOverlayManagerIpc(manager: OverlayWindowManager): void {
  ipcMain.handle(OVERLAY_IPC.setInteractive, (_event, interactive: boolean) =>
    manager.setAllInteractive(interactive)
  );
  ipcMain.handle(OVERLAY_IPC.copyText, (_event, text: string) => {
    clipboard.writeText(text);
    return true;
  });
  ipcMain.handle(OVERLAY_IPC.getState, () => manager.getState());
  ipcMain.handle(OVERLAY_IPC.toggleControlCard, () => manager.toggleControlCard());
  ipcMain.handle(OVERLAY_IPC.openControlCard, () => manager.openControlCard());
  ipcMain.handle(OVERLAY_IPC.closeControlCard, () => manager.closeControlCard());
  ipcMain.handle(OVERLAY_IPC.openPopover, (_event, payload: OpenPopoverPayload) =>
    manager.openPopover(payload)
  );
  ipcMain.handle(OVERLAY_IPC.closePopover, () => manager.closePopover());
  ipcMain.handle(OVERLAY_IPC.escape, () => manager.escape());
  ipcMain.handle(OVERLAY_IPC.settingSelected, (_event, payload: SettingSelectedPayload) =>
    manager.settingSelected(payload)
  );
}
