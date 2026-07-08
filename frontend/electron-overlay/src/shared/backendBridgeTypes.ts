export type SubtitleKind = "partial" | "final" | "clear";
export type RuntimeStatus = "idle" | "starting" | "running" | "stopping" | "error";
export type CommandName =
  | "start"
  | "stop"
  | "setDisplayMode"
  | "setTargetLanguage"
  | "setSourceLanguage"
  | "setTranslationModel";

export interface SubtitleEvent {
  type: "subtitle";
  segmentId: number;
  kind: SubtitleKind;
  source: string;
  translation: string;
  sourceLang: "auto" | "en" | "ja" | string;
  targetLang: "zh-TW" | "zh-CN";
  latencyMs?: number;
  timestampMs: number;
}

export interface StatusEvent {
  type: "status";
  status: RuntimeStatus;
  backendConnected: boolean;
  detail?: string;
}

export interface SettingsEvent {
  type: "settings";
  showSource?: boolean;
  showTranslation?: boolean;
  sourceLang?: "auto" | "en" | "ja";
  targetLang?: "zh-TW" | "zh-CN";
  translationModel?: "deepseek-v4-flash" | "deepseek-v4-pro";
}

export interface CommandMessage {
  type: "command";
  command: CommandName;
  value?: string | boolean;
  requestId: string;
}

export type BackendEvent = SubtitleEvent | StatusEvent | SettingsEvent;
