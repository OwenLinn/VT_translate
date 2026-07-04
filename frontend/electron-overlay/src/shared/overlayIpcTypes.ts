export type OverlayMode = "mock" | "tuning";
export type OverlayWindowMode = "multi" | "single_legacy";
export type OverlayWindowType = "subtitle" | "settings-icon" | "control-card" | "popover";
export type RuntimeStatus = "idle" | "starting" | "running" | "stopping" | "error";
export type SubtitleKind = "partial" | "final";
export type ActivePopover = "display" | "language" | "model" | "tuning" | null;
export type DisplayMode = "translation" | "source-translation" | "source";

export interface OverlayBounds {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface OverlayUiState {
  running: boolean;
  backendConnected: boolean;
  runtimeStatus: RuntimeStatus;
  activePreset: string;
  sourceLanguage: "auto" | "en" | "ja";
  targetLanguage: "zh-TW" | "zh-CN";
  asrModel: string;
  deepseekModel: "deepseek-v4-flash" | "deepseek-v4-pro";
  displayMode: DisplayMode;
  showControlCard: boolean;
  activePopover: ActivePopover;
  subtitle: {
    sourceText: string;
    translatedText: string;
    isPartial: boolean;
    segmentId: number;
    latencyMs: number | null;
  };
}

export interface OverlayPositionSnapshot {
  subtitle: OverlayBounds;
  settingsIcon: OverlayBounds;
  controlCard: OverlayBounds;
  popover: OverlayBounds;
}

export interface OpenPopoverPayload {
  popover: Exclude<ActivePopover, null>;
  rowOffset?: number;
}

export interface SettingSelectedPayload {
  key:
    | "running"
    | "displayMode"
    | "sourceLanguage"
    | "targetLanguage"
    | "deepseekModel"
    | "activePreset";
  value: string | boolean;
}

export interface OverlayRendererApi {
  setInteractive: (interactive: boolean) => Promise<boolean>;
  copyText: (text: string) => Promise<boolean>;
  getState: () => Promise<OverlayUiState>;
  toggleControlCard: () => Promise<OverlayUiState>;
  openControlCard: () => Promise<OverlayUiState>;
  closeControlCard: () => Promise<OverlayUiState>;
  openPopover: (payload: OpenPopoverPayload) => Promise<OverlayUiState>;
  closePopover: () => Promise<OverlayUiState>;
  escape: () => Promise<OverlayUiState>;
  settingSelected: (payload: SettingSelectedPayload) => Promise<OverlayUiState>;
  onStateUpdated: (callback: (state: OverlayUiState) => void) => () => void;
  onPositionUpdated: (callback: (positions: OverlayPositionSnapshot) => void) => () => void;
}

export const OVERLAY_IPC = {
  setInteractive: "overlay:set-interactive",
  copyText: "overlay:copy-text",
  getState: "overlay:get-state",
  toggleControlCard: "overlay:toggle-control-card",
  openControlCard: "overlay:open-control-card",
  closeControlCard: "overlay:close-control-card",
  openPopover: "overlay:open-popover",
  closePopover: "overlay:close-popover",
  updateWindowPosition: "overlay:update-window-position",
  dragStart: "overlay:drag-start",
  dragMove: "overlay:drag-move",
  dragEnd: "overlay:drag-end",
  escape: "overlay:escape",
  settingSelected: "overlay:setting-selected",
  stateUpdated: "overlay:state-updated",
  popoverContent: "overlay:popover-content",
  positionUpdated: "overlay:position-updated",
  subtitleEvent: "overlay:subtitle-event"
} as const;
