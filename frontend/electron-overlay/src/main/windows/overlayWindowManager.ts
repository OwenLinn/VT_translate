import { BrowserWindow } from "electron";
import type { BackendEvent, CommandName } from "../../shared/backendBridgeTypes";
import type {
  ActivePopover,
  DisplayMode,
  OpenPopoverPayload,
  OverlayBounds,
  OverlayMode,
  OverlayPositionSnapshot,
  OverlayUiState,
  OverlayWindowType,
  SettingSelectedPayload
} from "../../shared/overlayIpcTypes";
import { OVERLAY_IPC } from "../../shared/overlayIpcTypes";
import { createControlCardWindow } from "./controlCardWindow";
import { createPopoverWindow } from "./popoverWindow";
import { createSettingsIconWindow } from "./settingsIconWindow";
import { createSubtitleWindow } from "./subtitleWindow";
import { initialSubtitleBounds, layoutFromSubtitle } from "./windowGeometry";

type WindowMap = Partial<Record<OverlayWindowType, BrowserWindow>>;
type BackendCommandSender = (command: CommandName, value?: string | boolean) => boolean;

const mockLines = [
  {
    sourceText: "The live streamer is setting up the next match...",
    translatedText: "Mock translation: preparing the next match...",
    isPartial: true,
    latencyMs: 1180
  },
  {
    sourceText: "The live streamer is setting up the next match and checking chat.",
    translatedText: "Mock translation: preparing the next match and checking chat.",
    isPartial: false,
    latencyMs: 1740
  },
  {
    sourceText: "This boss phase looks dangerous.",
    translatedText: "Mock translation: this boss phase looks dangerous.",
    isPartial: true,
    latencyMs: 1320
  },
  {
    sourceText: "This boss phase looks dangerous, but the timing is clean.",
    translatedText: "Mock translation: dangerous phase, clean timing.",
    isPartial: false,
    latencyMs: 2030
  }
] as const;

export class OverlayWindowManager {
  private windows: WindowMap = {};
  private positions: OverlayPositionSnapshot;
  private state: OverlayUiState;
  private mockTimer: NodeJS.Timeout | null = null;
  private mockIndex = 0;
  private movingAnchoredWindows = false;
  private activePopoverRowOffset = 58;
  private sendBackendCommand: BackendCommandSender | null = null;

  constructor(
    private readonly mode: OverlayMode,
    private readonly useMockEvents = true
  ) {
    const subtitle = initialSubtitleBounds();
    this.positions = layoutFromSubtitle(subtitle, { tuning: mode === "tuning" });
    this.state = {
      running: true,
      backendConnected: false,
      runtimeStatus: useMockEvents ? "running" : "idle",
      activePreset: "cleanDark",
      sourceLanguage: "auto",
      targetLanguage: "zh-TW",
      asrModel: "models/faster-whisper-large-v3",
      deepseekModel: "deepseek-v4-flash",
      displayMode: "source-translation",
      showControlCard: false,
      activePopover: null,
      subtitle: {
        sourceText: "Streamer audio mock input is waiting for the live pipeline.",
        translatedText: useMockEvents ? "Electron multi-window mock subtitle." : "Waiting for live translation.",
        isPartial: false,
        segmentId: 0,
        latencyMs: 0
      }
    };
  }

  createAll(): void {
    this.windows.subtitle = createSubtitleWindow(this.mode, this.positions.subtitle);
    this.windows["settings-icon"] = createSettingsIconWindow(this.mode, this.positions.settingsIcon);
    this.windows["control-card"] = createControlCardWindow(this.mode, this.positions.controlCard);
    this.windows.popover = createPopoverWindow(this.mode, this.positions.popover);

    this.windows.subtitle.on("moved", () => this.handleSubtitleMoved());
    this.windows.subtitle.on("resized", () => this.handleSubtitleMoved());

    for (const win of Object.values(this.windows)) {
      win?.webContents.once("did-finish-load", () => {
        this.broadcastState();
        this.broadcastPositions();
      });
    }

    if (this.useMockEvents) {
      this.startMockEvents();
    }
  }

  getWindow(type: OverlayWindowType): BrowserWindow | null {
    return this.windows[type] ?? null;
  }

  getFocusedWindow(): BrowserWindow | null {
    return BrowserWindow.getFocusedWindow();
  }

  getState(): OverlayUiState {
    return this.state;
  }

  setBackendCommandSender(sender: BackendCommandSender): void {
    this.sendBackendCommand = sender;
  }

  applyBackendEvent(event: BackendEvent): void {
    if (event.type === "subtitle") {
      const partial = event.kind === "partial";
      console.log(
        `[manager] subtitle ${event.kind} seg=${event.segmentId} src="${event.source.slice(0, 40)}" tr="${event.translation.slice(0, 40)}" latency=${event.latencyMs}ms`
      );
      this.patchState({
        backendConnected: true,
        runtimeStatus: "running",
        running: true,
        sourceLanguage: normalizeSourceLanguage(event.sourceLang),
        targetLanguage: event.targetLang,
        subtitle: {
          sourceText: event.source,
          translatedText: event.translation,
          isPartial: partial,
          segmentId: event.segmentId,
          latencyMs: event.latencyMs ?? null
        }
      });
      return;
    }
    if (event.type === "status") {
      console.log(
        `[manager] status status=${event.status} connected=${event.backendConnected} detail="${event.detail ?? ""}"`
      );
      this.patchState({
        backendConnected: event.backendConnected,
        runtimeStatus: event.status,
        running: event.status === "starting" || event.status === "running"
      });
      return;
    }
    console.log(
      `[manager] settings srcLang=${event.sourceLang ?? "-"} tgtLang=${event.targetLang ?? "-"} model=${event.translationModel ?? "-"}`
    );
    this.patchState({
      sourceLanguage: event.sourceLang ?? this.state.sourceLanguage,
      targetLanguage: event.targetLang ?? this.state.targetLanguage,
      deepseekModel: event.translationModel ?? this.state.deepseekModel,
      displayMode:
        event.showSource === false
          ? "translation"
          : event.showTranslation === false
            ? "source"
            : this.state.displayMode
    });
  }

  setBackendConnected(connected: boolean, detail?: string): void {
    this.patchState({
      backendConnected: connected,
      runtimeStatus: connected ? this.state.runtimeStatus : "idle",
      subtitle: connected
        ? this.state.subtitle
        : {
            ...this.state.subtitle,
            translatedText: detail ? `Waiting for backend: ${detail}` : "Waiting for backend connection."
          }
    });
  }

  setAllInteractive(interactive: boolean): boolean {
    for (const win of Object.values(this.windows)) {
      win?.setIgnoreMouseEvents(!interactive, { forward: true });
    }
    return true;
  }

  toggleControlCard(): OverlayUiState {
    const opening = !this.state.showControlCard;
    console.log(`[manager] toggleControlCard opening=${opening}`);
    return this.state.showControlCard ? this.closeControlCard() : this.openControlCard();
  }

  openControlCard(): OverlayUiState {
    this.relayout();
    this.applyBounds();
    this.patchState({ showControlCard: true });
    this.syncWindowVisibility();
    return this.state;
  }

  closeControlCard(): OverlayUiState {
    this.patchState({ showControlCard: false, activePopover: null });
    this.syncWindowVisibility();
    return this.state;
  }

  openPopover(payload: OpenPopoverPayload): OverlayUiState {
    this.activePopoverRowOffset = payload.rowOffset ?? this.activePopoverRowOffset;
    this.relayout(payload.popover);
    this.applyBounds();
    this.patchState({
      showControlCard: true,
      activePopover: payload.popover
    });
    this.syncWindowVisibility();
    return this.state;
  }

  closePopover(): OverlayUiState {
    this.patchState({ activePopover: null });
    this.syncWindowVisibility();
    return this.state;
  }

  escape(): OverlayUiState {
    if (this.state.activePopover) {
      return this.closePopover();
    }
    if (this.state.showControlCard) {
      return this.closeControlCard();
    }
    return this.state;
  }

  settingSelected(payload: SettingSelectedPayload): OverlayUiState {
    switch (payload.key) {
      case "running":
        this.patchState({
          running: Boolean(payload.value),
          runtimeStatus: payload.value ? "running" : "idle"
        });
        this.sendBackendCommand?.(payload.value ? "start" : "stop");
        break;
      case "displayMode":
        this.patchState({ displayMode: payload.value as DisplayMode });
        this.sendBackendCommand?.("setDisplayMode", String(payload.value));
        break;
      case "sourceLanguage":
        this.patchState({ sourceLanguage: payload.value as OverlayUiState["sourceLanguage"] });
        this.sendBackendCommand?.("setSourceLanguage", String(payload.value));
        break;
      case "targetLanguage":
        this.patchState({ targetLanguage: payload.value as OverlayUiState["targetLanguage"] });
        this.sendBackendCommand?.("setTargetLanguage", String(payload.value));
        break;
      case "deepseekModel":
        this.patchState({ deepseekModel: payload.value as OverlayUiState["deepseekModel"] });
        this.sendBackendCommand?.("setTranslationModel", String(payload.value));
        break;
      case "activePreset":
        this.patchState({ activePreset: String(payload.value) });
        break;
    }
    return this.state;
  }

  updateSubtitleBounds(bounds: OverlayBounds): void {
    this.relayout(this.state.activePopover, bounds);
    this.applyBounds();
    this.broadcastPositions();
  }

  destroy(): void {
    if (this.mockTimer) {
      clearInterval(this.mockTimer);
      this.mockTimer = null;
    }
    for (const win of Object.values(this.windows)) {
      if (win && !win.isDestroyed()) {
        win.destroy();
      }
    }
  }

  private startMockEvents(): void {
    this.emitNextMockSubtitle();
    this.mockTimer = setInterval(() => this.emitNextMockSubtitle(), 2600);
  }

  private emitNextMockSubtitle(): void {
    const line = mockLines[this.mockIndex % mockLines.length];
    this.mockIndex += 1;
    this.patchState({
      subtitle: {
        ...line,
        segmentId: this.mockIndex
      }
    });
  }

  private patchState(patch: Partial<OverlayUiState>): void {
    this.state = {
      ...this.state,
      ...patch
    };
    this.broadcastState();
  }

  private syncWindowVisibility(): void {
    const control = this.windows["control-card"];
    const popover = this.windows.popover;
    if (this.state.showControlCard) {
      control?.show();
      control?.moveTop();
    } else {
      control?.hide();
    }

    if (this.state.showControlCard && this.state.activePopover) {
      popover?.show();
      popover?.moveTop();
    } else {
      popover?.hide();
    }
  }

  private handleSubtitleMoved(): void {
    if (this.movingAnchoredWindows) {
      return;
    }
    const subtitle = this.windows.subtitle;
    if (!subtitle || subtitle.isDestroyed()) {
      return;
    }
    this.updateSubtitleBounds(subtitle.getBounds());
  }

  private relayout(
    activePopover: ActivePopover = this.state.activePopover,
    subtitle = this.positions.subtitle
  ): void {
    this.positions = layoutFromSubtitle(subtitle, {
      tuning: this.mode === "tuning",
      rowOffset: this.activePopoverRowOffset,
      activePopover
    });
  }

  private applyBounds(): void {
    this.movingAnchoredWindows = true;
    this.windows["settings-icon"]?.setBounds(this.positions.settingsIcon);
    this.windows["control-card"]?.setBounds(this.positions.controlCard);
    this.windows.popover?.setBounds(this.positions.popover);
    this.movingAnchoredWindows = false;
  }

  private broadcastState(): void {
    this.broadcast(OVERLAY_IPC.stateUpdated, this.state);
  }

  private broadcastPositions(): void {
    this.broadcast(OVERLAY_IPC.positionUpdated, this.positions);
  }

  private broadcast(channel: string, payload: unknown): void {
    for (const win of Object.values(this.windows)) {
      if (win && !win.isDestroyed()) {
        win.webContents.send(channel, payload);
      }
    }
  }
}

function normalizeSourceLanguage(language: string): OverlayUiState["sourceLanguage"] {
  if (language === "en" || language === "ja") {
    return language;
  }
  return "auto";
}
