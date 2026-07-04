import { create } from "zustand";
import type { BackendEvent, RuntimeStatus, SubtitleEvent } from "../bridge/messageTypes";
import type { OverlayUiState } from "../../shared/overlayIpcTypes";

export type DisplayMode = "translation" | "source-translation" | "source";
export type PopoverKind = "display" | "language" | "model" | null;

interface OverlayState {
  source: string;
  translation: string;
  subtitleKind: "partial" | "final";
  segmentId: number;
  latencyMs: number | null;
  status: RuntimeStatus;
  backendConnected: boolean;
  showSource: boolean;
  showTranslation: boolean;
  sourceLang: "auto" | "en" | "ja";
  targetLang: "zh-TW" | "zh-CN";
  translationModel: "deepseek-v4-flash" | "deepseek-v4-pro";
  controlOpen: boolean;
  popover: PopoverKind;
  displayMode: DisplayMode;
  applyEvent: (event: BackendEvent) => void;
  setRunning: (running: boolean) => void;
  setControlOpen: (open: boolean) => void;
  setPopover: (popover: PopoverKind) => void;
  setDisplayMode: (mode: DisplayMode) => void;
  setTargetLang: (targetLang: "zh-TW" | "zh-CN") => void;
  setSourceLang: (sourceLang: "auto" | "en" | "ja") => void;
  setTranslationModel: (model: "deepseek-v4-flash" | "deepseek-v4-pro") => void;
  applyUiState: (state: OverlayUiState) => void;
}

const initialSubtitle: Pick<
  OverlayState,
  "source" | "translation" | "subtitleKind" | "segmentId" | "latencyMs"
> = {
  source: "Streamer audio mock input is waiting for the live pipeline.",
  translation: "Electron Liquid Glass Phase 2 mock subtitle.",
  subtitleKind: "final",
  segmentId: 0,
  latencyMs: 0
};

function displayFlags(mode: DisplayMode): Pick<OverlayState, "showSource" | "showTranslation"> {
  return {
    showSource: mode !== "translation",
    showTranslation: mode !== "source"
  };
}

function applySubtitle(event: SubtitleEvent): Partial<OverlayState> {
  return {
    source: event.source,
    translation: event.translation,
    subtitleKind: event.kind,
    segmentId: event.segmentId,
    latencyMs: event.latencyMs ?? null,
    sourceLang: normalizeSourceLanguage(event.sourceLang),
    targetLang: event.targetLang
  };
}

function normalizeSourceLanguage(language: string): OverlayState["sourceLang"] {
  if (language === "en" || language === "ja") {
    return language;
  }
  return "auto";
}

export const useOverlayStore = create<OverlayState>((set) => ({
  ...initialSubtitle,
  status: "idle",
  backendConnected: false,
  showSource: true,
  showTranslation: true,
  sourceLang: "auto",
  targetLang: "zh-TW",
  translationModel: "deepseek-v4-flash",
  controlOpen: false,
  popover: null,
  displayMode: "source-translation",
  applyEvent: (event) => {
    if (event.type === "subtitle") {
      set(applySubtitle(event));
      return;
    }
    if (event.type === "status") {
      set({
        status: event.status,
        backendConnected: event.backendConnected
      });
      return;
    }
    set((state) => ({
      showSource: event.showSource ?? state.showSource,
      showTranslation: event.showTranslation ?? state.showTranslation,
      sourceLang: event.sourceLang ?? state.sourceLang,
      targetLang: event.targetLang ?? state.targetLang,
      translationModel: event.translationModel ?? state.translationModel
    }));
  },
  setRunning: (running) =>
    set({
      status: running ? "running" : "idle"
    }),
  setControlOpen: (open) =>
    set({
      controlOpen: open,
      popover: open ? null : null
    }),
  setPopover: (popover) => set({ popover }),
  setDisplayMode: (mode) =>
    set({
      displayMode: mode,
      ...displayFlags(mode)
    }),
  setTargetLang: (targetLang) => set({ targetLang }),
  setSourceLang: (sourceLang) => set({ sourceLang }),
  setTranslationModel: (translationModel) => set({ translationModel }),
  applyUiState: (state) =>
    set({
      source: state.subtitle.sourceText,
      translation: state.subtitle.translatedText,
      subtitleKind: state.subtitle.isPartial ? "partial" : "final",
      segmentId: state.subtitle.segmentId,
      latencyMs: state.subtitle.latencyMs,
      status: state.runtimeStatus,
      backendConnected: state.backendConnected,
      showSource: state.displayMode !== "translation",
      showTranslation: state.displayMode !== "source",
      sourceLang: state.sourceLanguage,
      targetLang: state.targetLanguage,
      translationModel: state.deepseekModel,
      controlOpen: state.showControlCard,
      popover: state.activePopover === "tuning" ? null : state.activePopover,
      displayMode: state.displayMode
    })
}));
