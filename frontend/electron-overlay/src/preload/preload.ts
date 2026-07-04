import { contextBridge, ipcRenderer } from "electron";
import type {
  OpenPopoverPayload,
  OverlayPositionSnapshot,
  OverlayRendererApi,
  OverlayUiState,
  SettingSelectedPayload
} from "../shared/overlayIpcTypes";
import { OVERLAY_IPC } from "../shared/overlayIpcTypes";

const api: OverlayRendererApi = {
  setInteractive: (interactive: boolean): Promise<boolean> =>
    ipcRenderer.invoke(OVERLAY_IPC.setInteractive, interactive),
  copyText: (text: string): Promise<boolean> => ipcRenderer.invoke(OVERLAY_IPC.copyText, text),
  getState: (): Promise<OverlayUiState> => ipcRenderer.invoke(OVERLAY_IPC.getState),
  toggleControlCard: (): Promise<OverlayUiState> => ipcRenderer.invoke(OVERLAY_IPC.toggleControlCard),
  openControlCard: (): Promise<OverlayUiState> => ipcRenderer.invoke(OVERLAY_IPC.openControlCard),
  closeControlCard: (): Promise<OverlayUiState> => ipcRenderer.invoke(OVERLAY_IPC.closeControlCard),
  openPopover: (payload: OpenPopoverPayload): Promise<OverlayUiState> =>
    ipcRenderer.invoke(OVERLAY_IPC.openPopover, payload),
  closePopover: (): Promise<OverlayUiState> => ipcRenderer.invoke(OVERLAY_IPC.closePopover),
  escape: (): Promise<OverlayUiState> => ipcRenderer.invoke(OVERLAY_IPC.escape),
  settingSelected: (payload: SettingSelectedPayload): Promise<OverlayUiState> =>
    ipcRenderer.invoke(OVERLAY_IPC.settingSelected, payload),
  onStateUpdated: (callback: (state: OverlayUiState) => void): (() => void) => {
    const listener = (_event: Electron.IpcRendererEvent, state: OverlayUiState): void => callback(state);
    ipcRenderer.on(OVERLAY_IPC.stateUpdated, listener);
    return () => ipcRenderer.removeListener(OVERLAY_IPC.stateUpdated, listener);
  },
  onPositionUpdated: (callback: (positions: OverlayPositionSnapshot) => void): (() => void) => {
    const listener = (
      _event: Electron.IpcRendererEvent,
      positions: OverlayPositionSnapshot
    ): void => callback(positions);
    ipcRenderer.on(OVERLAY_IPC.positionUpdated, listener);
    return () => ipcRenderer.removeListener(OVERLAY_IPC.positionUpdated, listener);
  }
};

contextBridge.exposeInMainWorld("electronOverlay", api);

export type ElectronOverlayApi = typeof api;
